import numpy
try:
    import scipy.sparse as sp
    import scipy.sparse
except ImportError:
    pass  # The variable enable_sparse will be used to disable the test file.

import theano
from theano import config, tensor
from theano.sparse import enable_sparse
from theano.gof.python25 import any
if not enable_sparse:
    raise SkipTest('Optional package sparse disabled')

from theano.sparse import (CSM, CSMProperties, csm_properties, CSC, CSR,
                           DenseFromSparse, CSMGrad)
from theano.sparse.tests.test_basic import random_lil


def test_local_csm_properties_csm():
    data = tensor.vector()
    indices, indptr, shape = (tensor.ivector(), tensor.ivector(),
                              tensor.ivector())
    mode = theano.compile.mode.get_default_mode()
    mode = mode.including("specialize", "local_csm_properties_csm")
    for CS, cast in [(CSC, sp.csc_matrix), (CSR, sp.csr_matrix)]:
        f = theano.function([data, indices, indptr, shape],
                            csm_properties(CS(data, indices, indptr, shape)),
                            mode=mode)
        #theano.printing.debugprint(f)
        assert not any(isinstance(node.op, (CSM, CSMProperties)) for node
                       in f.maker.env.toposort())
        v = cast(random_lil((10, 40),
                            config.floatX, 3))
        f(v.data, v.indices, v.indptr, v.shape)


def test_local_csm_grad_c():
    data = tensor.vector()
    indices, indptr, shape = (tensor.ivector(), tensor.ivector(),
                              tensor.ivector())
    mode = theano.compile.mode.get_default_mode()

    if theano.config.mode == 'FAST_COMPILE':
        mode = theano.compile.Mode(linker='c|py', optimizer='fast_compile')

    mode = mode.including("specialize", "local_csm_grad_c")
    for CS, cast in [(CSC, sp.csc_matrix), (CSR, sp.csr_matrix)]:
        cost = tensor.sum(DenseFromSparse()(CS(data, indices, indptr, shape)))
        f = theano.function(
            [data, indices, indptr, shape],
            tensor.grad(cost, data),
            mode=mode)
        assert not any(isinstance(node.op, CSMGrad) for node
                       in f.maker.env.toposort())
        v = cast(random_lil((10, 40),
                            config.floatX, 3))
        f(v.data, v.indices, v.indptr, v.shape)