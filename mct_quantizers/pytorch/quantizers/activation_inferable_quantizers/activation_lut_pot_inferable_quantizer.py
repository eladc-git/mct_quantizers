# Copyright 2023 Sony Semiconductor Israel, Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
import numpy as np

from mct_quantizers.common.base_inferable_quantizer import mark_quantizer, QuantizationTarget
from mct_quantizers.common.constants import FOUND_TORCH, MULTIPLIER_N_BITS, EPS
from mct_quantizers.common.quant_info import QuantizationMethod


if FOUND_TORCH:
    import torch
    from mct_quantizers.pytorch.quantizers.base_lut_symmetric_inferable_quantizer import BaseLUTSymmetricInferableQuantizer
    from mct_quantizers.pytorch.quantizer_utils import to_torch_tensor, get_working_device, lut_quantizer

    @mark_quantizer(quantization_target=QuantizationTarget.Activation,
                    quantization_method=[QuantizationMethod.LUT_POT_QUANTIZER],
                    quantizer_type=None)
    class ActivationLutPOTInferableQuantizer(BaseLUTSymmetricInferableQuantizer):
        """
        Class for quantizing activations using a lut power-of-two quantizer
        """

        def __init__(self,
                     num_bits: int,
                     cluster_centers: np.ndarray,
                     threshold: np.ndarray,
                     signed: bool,
                     multiplier_n_bits: int = MULTIPLIER_N_BITS,
                     eps: float = EPS):
            """
            Initialize the quantizer with the specified parameters.

            Args:
                num_bits: number of bits to use for quantization
                cluster_centers: the cluster centers to assign the activations
                threshold: threshold for quantizing activations
                signed: whether to use signed quantization or not
                multiplier_n_bits: Number of bits that determines the quantization range
                eps: Small value for numerical stability in division
            """

            super(ActivationLutPOTInferableQuantizer, self).__init__(
                num_bits=num_bits,
                cluster_centers=cluster_centers,
                threshold=threshold,
                signed=signed,
                multiplier_n_bits=multiplier_n_bits,
                eps=eps)

            is_threshold_pot = np.all(np.round(np.log2(threshold.flatten())) == np.log2(threshold.flatten()))
            assert is_threshold_pot, f'Expected threshold to be power of 2 but is {threshold}'

            # Activation supports only per-tensor quantization
            assert len(
                self.threshold) == 1, f'For activation, quantization per channel is not supported and threshold ' \
                                      f'should be of length 1 but is {len(threshold)}'
            self.threshold = self.threshold[0]

            self.cluster_centers = to_torch_tensor(self.cluster_centers).to(get_working_device())

        def __call__(self, inputs: torch.Tensor):
            """
            Quantize the given inputs using the quantizer parameters.

            Args:
                inputs: input tensor to quantize

            Returns:
                quantized tensor.
            """
            return lut_quantizer(inputs, cluster_centers=self.cluster_centers, signed=self.signed,
                                 threshold=self.threshold, multiplier_n_bits=self.multiplier_n_bits, eps=self.eps)

else:
    class ActivationLutPOTInferableQuantizer:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            raise Exception('Installing torch is mandatory '
                            'when using ActivationLutPOTInferableQuantizer. '
                            'Could not find torch package.')
