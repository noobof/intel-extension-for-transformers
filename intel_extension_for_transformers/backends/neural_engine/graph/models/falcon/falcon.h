//  Copyright (c) 2023 Intel Corporation
//
//  Licensed under the Apache License, Version 2.0 (the "License");
//  you may not use this file except in compliance with the License.
//  You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
//  Unless required by applicable law or agreed to in writing, software
//  distributed under the License is distributed on an "AS IS" BASIS,
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//  See the License for the specific language governing permissions and
//  limitations under the License.

#ifndef FALCON_H
#define FALCON_H

#include "models/model_utils/model_files.h"
#include "models/model_utils/model_types.h"

enum falcon_model {
  FALCON_UNKNOWN,
  FALCON_7B,
};

static const model_scratch falcon_mem_req(int n_layers) {
  switch (n_layers) {
    case 32:
      return {2048ull * MB, 2048ull * MB, 4096ull * MB, 3072ull * MB};
    // TODO(hengyu): add more variants besides 6B
    default:
      MODEL_ASSERT(false);
  }
}

class FALCON : public IModel {
 private:
  model_name name = MODEL_FALCON;
  std::unique_ptr<model_model_loader> ml;
  uint32_t n_layer, n_embd, n_ff, n_vocab;
  int n_ctx, n_gpu_layer;
  ne_type memory_type;
  bool use_mmap, use_mlock, vocab_only;
  model_scratch scratch;

 public:
  void init(const char* path_model, model_context& lctx, int n_ctx, int n_gpu_layers, ne_type memory_type_,
            bool use_mmap_, bool use_mlock_, bool vocab_only_) override;
  void load(model_context& lctx, model_progress_callback progress_callback, void* progress_callback_user_data) override;
};

#endif  // FALCON_H
