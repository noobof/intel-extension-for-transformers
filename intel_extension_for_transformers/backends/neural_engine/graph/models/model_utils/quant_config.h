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

#include <stdint.h>
#include <string>
#include "core/data_types.h"

enum class quant_bits : int { q4 = 0, q8, count };
static inline quant_bits parse_bits(int bits) {
  if (bits == 4) {
    return quant_bits::q4;
  }
  if (bits == 8) {
    return quant_bits::q8;
  }
  return quant_bits::count;
}

enum class quant_alg : int {
  sym = 0,
  asym,
  count,
};
static inline quant_alg parse_alg(std::string arg) {
  if (arg == "sym") {
    return quant_alg::sym;
  }
  if (arg == "asym") {
    return quant_alg::asym;
  }
  return quant_alg::count;
}

enum class quant_sdtype : int {
  fp16 = 0,
  fp32,
  bf16,
  count,
};
static inline quant_sdtype parse_scale_dtype(std::string arg) {
  if (arg == "fp16") {
    return quant_sdtype::fp16;
  }
  if (arg == "fp32") {
    return quant_sdtype::fp32;
  }
  if (arg == "bf16") {
    return quant_sdtype::bf16;
  }
  return quant_sdtype::count;
}

enum class quant_comp : int {
  ggml = 0,  // native
  int8,      // jblas int8
  fp32,      // jblas fp32
  bf16,      // jblas bf16
  count,
};
static inline quant_comp parse_compute_type(std::string arg) {
  if (arg == "ggml") {
    return quant_comp::ggml;
  }
  if (arg == "int8") {
    return quant_comp::int8;
  }
  if (arg == "fp32") {
    return quant_comp::fp32;
  }
  if (arg == "bf16") {
    return quant_comp::bf16;
  }
  return quant_comp::count;
}

struct quant_params_internal {
  quant_bits bits = quant_bits::q4;
  quant_alg alg = quant_alg::sym;
  int32_t block_size = 32;
  quant_sdtype scale_dtype = quant_sdtype::fp16;
  quant_comp compute_type = quant_comp::ggml;
  bool valid() const {
    return bits != quant_bits::count && alg != quant_alg::count && scale_dtype != quant_sdtype::count &&
           compute_type != quant_comp::count && block_size > 0;
  }
  std::string getstr() {
    return std::to_string(int(bits)) + "_" + std::to_string(int(alg)) + "_" + std::to_string(block_size) + "_" +
           std::to_string(int(scale_dtype)) + "_" + std::to_string(int(compute_type));
  }
};

static inline ne_type quant_params_to_type(const quant_params_internal& params) {
  if (params.compute_type == quant_comp::ggml) {
    if (params.bits == quant_bits::q4) {
      if (params.alg == quant_alg::sym) {
        return NE_TYPE_Q4_0;
      } else if (params.alg == quant_alg::asym) {
        return NE_TYPE_Q4_1;
      }
    } else if (params.bits == quant_bits::q8) {
      if (params.alg == quant_alg::sym) {
        return NE_TYPE_Q8_0;
      }
    }
  } else {
    return NE_TYPE_JBLAS;
  }
  return NE_TYPE_F32;
}

class quant_layer_base {
 public:
  virtual void set_global_config(int nthread, quant_params_internal param) {
    mNThread = nthread;
    mGCfg = param;
  }
  virtual quant_params_internal get_layer_config(std::string layername, std::vector<int64_t> ne, ne_type type) = 0;

 protected:
  quant_params_internal mGCfg;
  int mNThread;
};
