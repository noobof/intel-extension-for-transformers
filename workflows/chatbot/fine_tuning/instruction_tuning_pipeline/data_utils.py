import copy
import datasets
import re
from itertools import chain

IGNORE_INDEX = -100

def truncate_sequences(sequences, max_length):
    words_to_cut = sum(list(map(len, sequences))) - max_length
    if words_to_cut <= 0:
        return sequences

    while words_to_cut > 0 and len(sequences) > 0:
        words_to_cut -= len(sequences[0])
        sequences = sequences[1:]

    return sequences

class CompletionDataPreprocess:
    prompt_template = {
            "prompt_with_input": (
                "Below is an instruction that describes a task, paired with an input that provides further context. "
                "Write a response that appropriately completes the request.\n\n"
                "### Instruction:\n{instruction}\n\n### Input:\n{input}\n\n### Response:"
            ),
            "prompt_without_input": (
                "Below is an instruction that describes a task. "
                "Write a response that appropriately completes the request.\n\n"
                "### Instruction:\n{instruction}\n\n### Response:"
            ),
    }
    
    def create_data(self, examples):
        prompts = {}
        prompts["source"] = []
        prompts["target"] = []
        for example in examples:
            prompt_template = (
                self.prompt_template["prompt_with_input"]
                if example.get("input") is not None and example.get("input") != ""
                else self.prompt_template["prompt_without_input"]
            )
            source = prompt_template.format_map(example)
            prompts["source"].append(source)
            prompts["target"].append(example["output"])
        return prompts

    @staticmethod
    def tokenize_func(tokenizer, data_args, finetune_args):
        def tokenize(prompt, add_eos_token=True):
            results = tokenizer(
                    prompt,
                    truncation=True,
                    max_length=data_args.max_seq_length,
                    padding=False,
                    return_tensors=None,)
            for i in range(len(results["input_ids"])):
                if (results["input_ids"][i][-1] != tokenizer.eos_token_id \
                        and len(results["input_ids"][i]) < data_args.max_seq_length \
                        and add_eos_token \
                        ):
                    results["input_ids"][i].append(tokenizer.eos_token_id)
                    results["attention_mask"][i].append(1)
            results["labels"] = copy.deepcopy(results["input_ids"])
            results["input_id_len"] = [len(result) for result in results["input_ids"]]
            return results

        def preprocess_function(examples):
            st = [s + t for s, t in zip(examples["prompt_sources"], examples["prompt_targets"])]
            examples_tokenized = tokenize(st)
            input_ids = examples_tokenized["input_ids"]
            labels = examples_tokenized["labels"]
            if not finetune_args.train_on_inputs:
                sources_tokenized = tokenize(examples["prompt_sources"], add_eos_token=False)
                for label, source_len in zip(labels, sources_tokenized["input_id_len"]):
                    label[:source_len] = [IGNORE_INDEX] * source_len
            return dict(
                    input_ids=input_ids,
                    labels=labels,
                    attention_mask=examples_tokenized["attention_mask"],
                    )

        return preprocess_function


class ChatDataPreprocess:
    base_template = """### System:
    - You are a helpful assistant chatbot trained by Intel.
    - You answer questions.
    - You are excited to be able to help the user, but will refuse to do anything that could be considered harmful to the user.
    - You are more than just an information source, you are also able to write poetry, short stories, and make jokes.{eos_token}\n"""

    def __init__(self, eos_token):
        self.prompt_template = self.base_template.format_map({"eos_token": eos_token})
        self.user = "### User:\n"
        self.assistant = "### Assistant:\n"
        self.end = eos_token

    def create_data(self, examples):
        prompts = {}
        prompts["prompt_sources"] = []
        prompts["prompt_targets"] = []

        for conv in examples:
            conv = conv["messages"]
            prompt = self.prompt_template

            for j in range(0, len(conv) - 1, 2):
                u = conv[j]["content"]
                ass = conv[j+1]["content"]
                prompt = prompt + self.user + u + self.end + '\n' + self.assistant
                response = ass + self.end
                prompts["prompt_sources"].append(prompt)
                prompts["prompt_targets"].append(response)

                prompt += response + '\n'
        return prompts

    def tokenize_func(self, tokenizer, data_args, finetune_args):

        # special tokens
        assistant_tokens = tokenizer.tokenize(self.assistant)

        def preprocess_function(examples):

            instructions = [q.strip() for q in examples["prompt_sources"]]
            responses = [q.strip() for q in examples["prompt_targets"]]

            examples["input_ids"] = []
            examples["labels"] = []
            examples["attention_mask"] = []

            for instruction, response in zip(instructions, responses):
                header = re.findall(r"### System.*?{}".format(self.end), instruction, re.DOTALL)[0]
                convs = re.findall(r"### User.*?{0}|### Assistant.*?{0}".format(self.end), instruction, re.DOTALL)
                convs_tokens = [
                    tokenizer.tokenize(conv) + tokenizer.tokenize("\n")
                    for conv in convs
                ]
                header_tokens = tokenizer.tokenize(header) + tokenizer.tokenize("\n")

                max_input = data_args.max_source_length - len(header_tokens) - len(assistant_tokens)

                truncated_convs = truncate_sequences(convs_tokens,
                        max_input)

                if len(truncated_convs) == 0:
                    truncated_convs = [convs_tokens[-1][:max_input - 3] + convs_tokens[-1][-3:]]

                prompt_tokens = [header_tokens] + truncated_convs + [assistant_tokens]
                prompt_ids = [tokenizer.convert_tokens_to_ids(prompt_token) for prompt_token in prompt_tokens]
                prompt_ids = list(chain(*prompt_ids))

                resp_ids = tokenizer.convert_tokens_to_ids(tokenizer.tokenize(response.strip()))
                # keep last and eos_id
                max_resp = data_args.max_seq_length - len(prompt_ids) - 1
                if len(resp_ids) > max_resp:
                    resp_ids = resp_ids[:max_resp - 1] + resp_ids[-1:]

                input_ids = prompt_ids + resp_ids  + [tokenizer.eos_token_id]
                if not finetune_args.train_on_inputs:
                    labels = [-100] * len(prompt_ids) + resp_ids + [tokenizer.eos_token_id]
                else:
                    labels = prompt_ids + resp_ids + [tokenizer.eos_token_id]

                # padding
                input_len = len(input_ids)
                pad_len = data_args.max_seq_length - input_len
                input_ids = input_ids + [tokenizer.eos_token_id] * pad_len
                labels = labels + [-100] * pad_len
                attention_mask = [1] * input_len + [0] * pad_len

                assert len(input_ids) == data_args.max_seq_length
                assert len(prompt_ids) <= data_args.max_source_length
                assert len(labels) == len(input_ids) == len(attention_mask)

                examples["input_ids"].append(input_ids)
                examples["labels"].append(labels)
                examples["attention_mask"].append(attention_mask)

            return examples

        return preprocess_function


class SummarizationDataPreprocess:
    prompt_template = "\nSummarize the highlights of this article.\n"

    def tokenize_func(self, tokenizer, data_args, finetune_args):
        template_ids = tokenizer.convert_tokens_to_ids(tokenizer.tokenize(self.prompt_template))

        def preprocess_function(examples):

            articles = [q.strip() for q in examples["article"]]
            highlights = [q.strip() for q in examples["highlights"]]

            examples["input_ids"] = []
            examples["labels"] = []
            examples["attention_mask"] = []

            for article, highlight in zip(articles, highlights):
                max_input = data_args.max_source_length - len(template_ids)

                article_tokens = tokenizer.tokenize(article)[:max_input]
                prompt_ids = tokenizer.convert_tokens_to_ids(article_tokens) + template_ids

                max_resp = data_args.max_seq_length - len(prompt_ids) - 1
                resp_ids = tokenizer.convert_tokens_to_ids(tokenizer.tokenize(highlight))[:max_resp]

                input_ids = prompt_ids + resp_ids  + [tokenizer.eos_token_id]
                if not finetune_args.train_on_inputs:
                    labels = [-100] * len(prompt_ids) + resp_ids + [tokenizer.eos_token_id]
                else:
                    labels = prompt_ids + resp_ids + [tokenizer.eos_token_id]

                # padding
                input_len = len(input_ids)
                pad_len = data_args.max_seq_length - input_len
                input_ids = input_ids + [tokenizer.eos_token_id] * pad_len
                labels = labels + [-100] * pad_len
                attention_mask = [1] * input_len + [0] * pad_len

                assert len(input_ids) == data_args.max_seq_length
                assert len(prompt_ids) <= data_args.max_source_length
                assert len(labels) == len(input_ids) == len(attention_mask)

                examples["input_ids"].append(input_ids)
                examples["labels"].append(labels)
                examples["attention_mask"].append(attention_mask)

            return examples

        return preprocess_function


def preprocess_dataset(raw_datasets, tokenizer, data_args, finetune_args):

    if finetune_args.task == "chat":
        preprocess = ChatDataPreprocess(tokenizer.eos_token)
        new_datasets = datasets.DatasetDict()
        prompts = preprocess.create_data(raw_datasets["train_ift"])
        new_datasets["train"] = datasets.Dataset.from_dict(prompts)

        preprocess_fn = preprocess.tokenize_func(tokenizer, data_args, finetune_args)

        return new_datasets, preprocess_fn

    elif finetune_args.task == "summarization":
        preprocess = SummarizationDataPreprocess()
        preprocess_fn = preprocess.tokenize_func(tokenizer, data_args, finetune_args)
        return raw_datasets, preprocess_fn
    elif finetune_args.task == "completion":
        # default use alpaca template
        preprocess = CompletionDataPreprocess() 
        for key in raw_datasets:
            prompts = preprocess.create_data(raw_datasets[key])
            columns_to_be_removed = list(raw_datasets[key].features.keys())
            raw_datasets[key] = raw_datasets[key].add_column(
                    "prompt_sources", prompts["source"]
                    )
            raw_datasets[key] = raw_datasets[key].add_column(
                    "prompt_targets", prompts["target"]
                    )
            raw_datasets[key] = raw_datasets[key].remove_columns(columns_to_be_removed)

        preprocess_fn = preprocess.tokenize_func(tokenizer, data_args, finetune_args)

        return raw_datasets, preprocess_fn
    else:
        raise NotImplementedError(f'finetune task data preprocessing is not support currently.')
