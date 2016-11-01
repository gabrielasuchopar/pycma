"""Very few interface defining base class definitions"""
from __future__ import absolute_import, division, print_function  #, unicode_literals
import numpy as np
del absolute_import, division, print_function  #, unicode_literals

class OOOptimizer(object):
    """abstract base class for an Object Oriented Optimizer interface.

    Relevant methods are `__init__`, `ask`, `tell`, `optimize` and `stop`,
    and property `result`. Only `optimize` is fully implemented in this
    base class.

    Examples
    --------
    All examples minimize the function `elli`, the output is not shown.
    (A preferred environment to execute all examples is ``ipython``.)

    First we need::

        # CMAEvolutionStrategy derives from the OOOptimizer class
        from cma import CMAEvolutionStrategy
        from cma.fitness_functions import elli

    The shortest example uses the inherited method
    `OOOptimizer.optimize`::

        es = CMAEvolutionStrategy(8 * [0.1], 0.5).optimize(elli)

    The input parameters to `CMAEvolutionStrategy` are specific to this
    inherited class. The remaining functionality is based on interface
    defined by `OOOptimizer`. We might have a look at the result::

        print(es.result[0])  # best solution and
        print(es.result[1])  # its function value

    Virtually the same example can be written with an explicit loop
    instead of using `optimize`. This gives the necessary insight into
    the `OOOptimizer` class interface and entire control over the
    iteration loop::

        # a new CMAEvolutionStrategy instance
        optim = CMAEvolutionStrategy(9 * [0.5], 0.3)

        # this loop resembles optimize()
        while not optim.stop():  # iterate
            X = optim.ask()      # get candidate solutions
            f = [elli(x) for x in X]  # evaluate solutions
            #  in case do something else that needs to be done
            optim.tell(X, f)     # do all the real "update" work
            optim.disp(20)       # display info every 20th iteration
            optim.logger.add()   # log another "data line", non-standard

        # final output
        print('termination by', optim.stop())
        print('best f-value =', optim.result[1])
        print('best solution =', optim.result[0])
        optim.logger.plot()  # if matplotlib is available

    Details
    -------
    Most of the work is done in the methods `tell` or `ask`. The property
    `result` provides more useful output.

    """
    def __init__(self, xstart, **more_kwargs):
        """``xstart`` is a mandatory argument"""
        self.xstart = xstart
        self.more_kwargs = more_kwargs
        self.initialize()
    def initialize(self):
        """(re-)set to the initial state"""
        raise NotImplementedError('method initialize() must be implemented in derived class')
        self.countiter = 0
        self.xcurrent = np.array(self.xstart, copy=True)
    def ask(self, gradf=None, **more_args):
        """abstract method, AKA "get" or "sample_distribution", deliver
        new candidate solution(s), a list of "vectors"
        """
        raise NotImplementedError('method ask() must be implemented in derived class')
    def tell(self, solutions, function_values):
        """abstract method, AKA "update", pass f-values and prepare for
        next iteration
        """
        self.countiter += 1
        raise NotImplementedError('method tell() must be implemented in derived class')
    def stop(self):
        """abstract method, return satisfied termination conditions in a
        dictionary like ``{'termination reason': value, ...}`` or ``{}``.

        For example ``{'tolfun': 1e-12}``, or the empty dictionary ``{}``.
        """
        raise NotImplementedError('method stop() is not implemented')
    def disp(self, modulo=None):
        """abstract method, display some iteration infos if
        ``self.iteration_counter % modulo == 0``
        """
    @property
    def result(self):
        """abstract property, contain ``(x, f(x), ...)``, that is, the
        minimizer, its function value, ...
        """
        raise NotImplementedError('result property is not implemented')
        return [self.xcurrent]

    def optimize(self,
                 objective_fct,
                 maxfun=1e99,
                 iterations=None,
                 min_iterations=1,
                 args=(),
                 verb_disp=None,
                 callback=None):
        """find minimizer of ``objective_fct``.

        CAVEAT: the return value for `optimize` has changed to ``self``,
        allowing for a call like::

            solver = OOOptimizer(x0).optimize(f)

        and investigate the state of the solver.

        Arguments
        ---------

        ``objective_fct``
            function be to minimized
        ``maxfun``
            maximal number of function evaluations
        ``iterations``
            number of (maximal) iterations, while ``not self.stop()``,
            it can be useful to conduct only one iteration at a time.
        ``min_iterations``
            minimal number of iterations, even if ``not self.stop()``
        ``args``
            arguments passed to ``objective_fct``
        ``verb_disp``
            print to screen every ``verb_disp`` iteration, if `None`
            the value from ``self.logger`` is "inherited", if
            available.
        ``callback``
            callback function called like ``callback(self)`` or
            a list of call back functions called in the same way. If
            available, ``self.logger.add`` is added to this list.
            todo: currently there is no way to prevent this other than
            changing the code of `_prepare_callback_list`.

        ``return self``, that is, the `OOOptimizer` instance.

        Example
        -------
        >>> import cma
        >>> es = cma.CMAEvolutionStrategy(7 * [0.1], 0.1
        ...              ).optimize(cma.ff.rosen, verb_disp=100)
        ...                   #doctest: +ELLIPSIS
        (4_w,9)-aCMA-ES (mu_w=2.8,w_1=49%) in dimension 7 (seed=...)
        Iterat #Fevals   function value  axis ratio  sigma ...
            1      9 ...
            2     18 ...
            3     27 ...
          100    900 ...
        >>> cma.s.Mh.vequals_approximately(es.result[0], 7 * [1], 1e-5)
        True

        """
        assert iterations is None or min_iterations <= iterations

        callback = self._prepare_callback_list(callback)

        citer, cevals = 0, 0
        while not self.stop() or citer < min_iterations:
            if cevals >= maxfun or citer >= (iterations if iterations
                                                else np.inf):
                return self
            citer += 1

            X = self.ask()  # deliver candidate solutions
            fitvals = [objective_fct(x, *args) for x in X]
            cevals += len(fitvals)
            self.tell(X, fitvals)  # all the work is done here
            self.disp(verb_disp)
            for f in callback:
                f is None or f(self)

        # final output
        self._force_final_logging()

        if verb_disp:
            self.disp(1)
            print('termination by', self.stop())
            print('best f-value =', self.result[1])
            print('solution =', self.result[0])

        return self

    def _prepare_callback_list(self, callback):
        """return a list of callbacks including ``self.logger.add``.

        ``callback`` can be a `callable` or a `list` (or iterable) of
        callables. Otherwise a `ValueError` exception is raised.
        """
        if callback is None:
            callback = []
        if callable(callback):
            callback = [callback]
        try:
            callback = list(callback) + [self.logger.add]
        except AttributeError:
            pass
        try:
            for c in callback:
                if not callable(c):
                    raise ValueError("""callback argument %s is not
                        callable""" % str(c))
        except TypeError:
            raise ValueError("""callback argument must be a `callable` or
                iterable (e.g. a list of callables), after some processing
                it was %s""" % str(callback))
        return callback

    def _force_final_logging(self):
        """try force the logger to log NOW"""
        if not self.logger:
            return
        # TODO: this is very ugly, because it assumes modulo keyword
        # TODO: argument *and* modulo attribute to be available
        # However, we like to force logging now which might be otherwise
        # done in a witty sparse way.
        # the idea: modulo == 0 means never log, 1 means log now
        try:
            modulo = bool(self.logger.modulo)
        except AttributeError:
            modulo = 1  # could also be named force
        try:
            self.logger.add(self, modulo=modulo)
        except AttributeError:
            pass
        except TypeError:
            print('  suppressing the final call of the logger in ' +
                  'OOOptimizer.optimize (modulo keyword parameter not ' +
                  'available)')

class StatisticalModelSamplerWithZeroMeanBaseClass(object):
    """yet versatile base class to replace a sampler namely in
    `CMAEvolutionStrategy`"""
    def __init__(self, dimension):
        """pass dimension of the underlying sample space
        """
        raise NotImplementedError
    def sample(self, number, update=None):
        """return list of i.i.d. samples.

        :param number: is the number of samples.
        :param update: controls a possibly lazy update of the sampler.
        """
        raise NotImplementedError
    def update(self, vectors, weights):
        """``vectors`` is a list of samples, ``weights`` a corrsponding
        list of learning rates
        """
        raise NotImplementedError

    def parameters(self, weights):
        """return `dict` with (default) parameters, e.g., `c1` and `cmu`.

        :See also: `RecombinationWeights`"""
        try:
            if np.all(self.weights == weights):
                return self._parameters
        except AttributeError:
            pass
        self.weights = np.array(weights, copy=True)
        lam = len(weights)
        w = np.array([w for w in weights if w > 0])
        mueff = sum(w)**2 / sum(w**2)
        # todo: put here rather generic formula with degrees of freedom
        # todo: replace these base class computations with the appropriate
        c1 = np.min((1, lam / 6)) * 2 / ((self.dimension + 1.3)**2.0 +
                                         mueff)
        self._parameters = dict(
            c1=c1,
            cmu=np.min((1 - c1,
                        2 * (mueff - 2 + 1 / mueff) /
                        ((self.dimension + 2)**2 + 2 * mueff / 2)))
        )
        return self._parameters

    def norm(self, x):
        """return Mahalanobis norm of `x` w.r.t. the statistical model"""
        return sum(self.transform_inverse(x)**2)**0.5

    @property
    def condition_number(self):
        raise NotImplementedError

    @property
    def covariance_matrix(self):
        raise NotImplementedError

    @property
    def variances(self):
        """vector of coordinate-wise (marginal) variances"""
        raise NotImplementedError

    def transform(self, x):
        """transform ``x`` as implied from the distribution parameters"""
        raise NotImplementedError

    def transform_inverse(self, x):
        raise NotImplementedError

    def to_linear_transformation_inverse(self, reset=False):
        """return inverse of associated linear transformation"""
        raise NotImplementedError

    def to_linear_transformation(self, reset=False):
        """return associated linear transformation"""
        raise NotImplementedError

    def inverse_hessian_scalar_correction(self, mean, X, f):
        """return scalar correction ``alpha`` such that ``X`` and ``f``
        fit to ``f(x) = (x-mean) (alpha * C)**-1 (x-mean)``
        """
        raise NotImplementedError

    def __imul__(self, factor):
        raise NotImplementedError

class BaseDataLogger(object):
    """"abstract" base class for a data logger that can be used with an
    `OOOptimizer`.

    Not in extensive use, as their are not many different logger around.

    Details: attribute `modulo` is used in `OOOptimizer.optimize`.
    """
    def add(self, optim=None, more_data=[], **kwargs):
        """abstract method, add a "data point" from the state of ``optim``
        into the logger.

        the argument ``optim`` can be omitted if ``optim`` was
        ``register`` ()-ed before, acts like an event handler
        """
        raise NotImplementedError
    def register(self, optim, *args, **kwargs):
        """abstract method, register an optimizer ``optim``, only needed
        if `add` () is called without passing the ``optim`` argument
        """
        self.optim = optim
        return self
    def disp(self, *args, **kwargs):
        """display some data trace (not implemented)"""
        print('method BaseDataLogger.disp() not implemented, to be done in subclass ' + str(type(self)))
    def plot(self, *args, **kwargs):
        """plot data (not implemented)"""
        print('method BaseDataLogger.plot() is not implemented, to be done in subclass ' + str(type(self)))
    @property
    def data(self):
        """logged data in a dictionary (not implemented)"""
        print('method BaseDataLogger.data is not implemented, to be done in subclass ' + str(type(self)))