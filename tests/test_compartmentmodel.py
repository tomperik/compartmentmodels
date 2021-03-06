import pytest
import scipy as sp
import numpy as np

import timeit

# set up a fixture for the Compartment model

@pytest.fixture(scope='module')
def model():
    from compartmentmodels.compartmentmodels import CompartmentModel
    model = CompartmentModel()
    return model


@pytest.fixture(scope='module')
def preparedmodel():
    """ prepare a model instance with startdict, time, aif and curve, ready for fitting
    """

    from compartmentmodels.compartmentmodels import CompartmentModel
    startdict = {'F': 51.0, 'v': 11.2}

    time = np.linspace(0, 50, 100)
    aif = np.zeros_like(time)
    aif[(time > 5) & (time < 10)] = 1.0
    model = CompartmentModel(
        time=time, curve=np.zeros_like(time), aif=aif, startdict=startdict)
    # calculate a model curve
    model.curve = model.calc_modelfunction(model._fitparameters)
    return model
    

@pytest.fixture(scope='module')
def brainaif_onec():
    """ prepare a model instance with startdict, time, aif and synthetic curve +
    additional background noise, ready for fitting
    """
    from compartmentmodels.compartmentmodels import loaddata, savedata
    from compartmentmodels.compartmentmodels import CompartmentModel
    startdict = {'F': 51.0, 'v': 11.2}

    time, aif1, aif2 =loaddata(filename='tests/cerebralartery.csv')    
    # remove baseline signal
    aif = aif1 - aif1[0:5].mean()
    model = CompartmentModel(
        time=time, curve=aif, aif=aif, startdict=startdict)
    # calculate a model curve
    model.curve = model.calc_modelfunction(model._fitparameters)
    model.curve += 0.02 * aif.max() * np.random.randn(len(time))
    # number of bootstraps
    model.k=500  
    
    return model


@pytest.fixture(scope='module')
def lungaif_onec():
    """ prepare a model instance with startdict, time, aif and synthetic curve +
    additional background noise, ready for fitting
    """
    from compartmentmodels.compartmentmodels import loaddata, savedata
    from compartmentmodels.compartmentmodels import CompartmentModel
    startdict = {'F': 51.0, 'v': 11.2}

    t,c,a=loaddata(filename='tests/lung.csv')    
    time = t
    aif = a
    curve = c
    # remove baseline signal
    aif = aif - aif[0:5].mean()
    model = CompartmentModel(
        time=time, curve=curve, aif=aif, startdict=startdict)
    # calculate a model curve
    model.curve = model.calc_modelfunction(model._fitparameters)
    model.curve += 0.02 * aif.max() * np.random.randn(len(time))
    return model

@pytest.fixture(scope='module')
def realcurve():
    """ prepare a model instance with startdict, time, aif and real curve ready for
    fitting
    """
    from compartmentmodels.compartmentmodels import loaddata, savedata
    from compartmentmodels.compartmentmodels import CompartmentModel
    startdict = {'F': 51.0, 'v': 11.2}

    t,c,a=loaddata(filename='tests/lung.csv')    
    time = t
    aif = a
    # remove baseline signal
    curve = c - c[0:5].mean()
    model = CompartmentModel(
        time=time, curve=curve, aif=aif, startdict=startdict)
    #model.curve += 0.002 * curve.max() * np.random.randn(len(time))
    return model
    

def test_compartmentModel_has_string_representation(model):
    str_rep=model.__str__()
    
    assert str_rep # an empty string is False, all others are True




def test_compartmentModel_python_convolution(model):
    # load a curve that was calculated with pmi
    # 'aif' is a boxcar function;
    testfile = 'tests/convolutions.csv'
    with open(testfile) as f:
        header = f.readline()
    header = header.lstrip('# ').rstrip()

    header = header.split(',')
    lamdalist = [np.float(el) for el in (header[2:])]

    inarray = np.loadtxt(testfile)
    time = inarray[:, 0]
    aif = inarray[:, 1]

    model.time=time
    model.aif=aif

    for i, lam in enumerate(lamdalist):
        curve = inarray[:, i + 2]
        np.testing.assert_array_equal(model.convolution_w_exp(lam), curve,
                                      verbose=False)



def test_compartmentModel_convolution_with_exponential_zero(preparedmodel):
    """ Convolution with an exponential with time constant zero.

    the default implementation will crash here
    """
    int_vector=preparedmodel.intvector()
    conv_w_zero=preparedmodel.convolution_w_exp(0.0)

    np.testing.assert_array_equal(int_vector, conv_w_zero)

def test_compartmentModel_fftconvolution_with_exponential_zero(preparedmodel):
    """ Convolution with an exponential with time constant zero.

    the default implementation will crash here
    """
    int_vector=preparedmodel.intvector()
    conv_w_zero=preparedmodel.convolution_w_exp(0.0, fftconvolution=True)

    np.testing.assert_array_equal(int_vector, conv_w_zero)
    
def do_not_test_compartmentModel_cpython_vs_fft_convolution(model):
    """ TEst whether a fft convolution yields the same result as the cpython
    implementation of the discrete convolution

    to do: this is currently not tested - we need some research first (issue #17)
    """
    testfile = 'tests/convolutions.csv'

    with open(testfile) as f:
        header = f.readline()
    header = header.lstrip('# ').rstrip()

    header = header.split(',')
    lamdalist = [np.float(el) for el in (header[2:])]

    inarray = np.loadtxt(testfile)
    time = inarray[:, 0]
    aif = inarray[:, 1]

    model.set_time(time)
    model.set_aif(aif)

    for i, lam in enumerate(lamdalist):
        # this curve was calcualted with the cpython convolution
        curve = inarray[:, i + 2]

        np.testing.assert_array_equal(model.convolution_w_exp(lam, fftconvolution=True),
        curve,verbose=False)


def do_not_test_compartmentModel_fftconvolution_equal_to_python_convolution(model):
    """ Test whether sp.fftconvolve yields a similar result to the discrete
    convolution
    to do: this is currently not tested - we need some research first (issue #17)
    """

    time = np.linspace(0, 50, 2000)
    aif = np.zeros_like(time)
    aif[(time > 5) & (time < 15)] = 1

    model.set_time(time)
    model.set_aif(aif)

    lamdalist = [4.2, 3.9, 0.1]

    for i, lam in enumerate(lamdalist):

        np.testing.assert_array_equal(model.convolution_w_exp(lam, fftconvolution=True),
        model.convolution_w_exp(lam, fftconvolution=False),verbose=False)


def test_compartmentModel_readableParameters_contain_all_keys(preparedmodel):
    assert all([k in preparedmodel.phys_parameters for k in ("F", "v")])

def test_compartmentModel_fit_model_returns_bool(preparedmodel):
    """Test whether the fit routine reports sucess of fitting
    """

    return_value = preparedmodel.fit_model()

    assert (isinstance(return_value, bool))


def test_compartmentModel_start_parameter_conversion(preparedmodel):
    """ are the startparameters converted correctly to raw parameters?

    First, we check manually.
    """

    original_startdict= {'F': 51.0, 'v': 11.2}

    raw_flow=original_startdict.get("F")/6000
    raw_vol=original_startdict.get("v") / 100
    lamda= raw_flow/raw_vol

    par=preparedmodel._fitparameters
    assert (par[0] == raw_flow) & (par[1] == lamda)

    
def test_compartmentmodel_fit_to_phys_returns_list_when_requested(preparedmodel):
    """ Does model._fit_to_phys return a list or a dictionary, as expected?
    """
    return_list = preparedmodel._fit_to_phys(aslist=True)
    assert (type(return_list) == list)
    return_none = preparedmodel._fit_to_phys()
    assert (type(return_none) == type(None))


def test_compartmentModel_parameter_conversion(preparedmodel):
    """ check the conversions from physiological to raw, and back
    """
    
    original_startdict= {'F': 51.0, 'v': 11.2}
    raw_par= preparedmodel._fitparameters

    
    # convert the fit parameters to physiological parameters 
    preparedmodel._fit_to_phys() 
    phys_parameters= preparedmodel.phys_parameters
    # test whether the dictionaries contain i) the same keys and ii) the corresponding values are equal. All keys from the start dict have to be in the output dict. Additionally, the readable_dict may contain additional keys, which are not checked.
    for key, value in original_startdict.iteritems():
        if key in phys_parameters:
            assert np.allclose(original_startdict.get(key) , phys_parameters.get(key))
        else:
            assert False, "Key {} is not contained in readable dictionary".format(key)


def test_compartmentModel_startdict_is_saved_appropriately(preparedmodel):
    """ is the startdict from constructor saved correctly?
    """

    original_startdict = {'F': 51.0, 'v': 11.2}
    readable_dict=preparedmodel.phys_parameters
    # we need to check whether all original keys/values are contained in the model parameter dict:
    for key, value in original_startdict.iteritems():
        if key in readable_dict:
            assert np.allclose(original_startdict.get(key), readable_dict.get(key))
        else:
            assert False,  "Key {} is not contained in readable dictionary".format(key)




def test_compartmentModel_fit_model_determines_right_parameters(preparedmodel):
    """ Are the fitted parameters the same as the initial parameters?
    This might become a longer test case...
    """

    start_parameters=preparedmodel._fitparameters
    return_value = preparedmodel.fit_model()

    assert np.allclose(preparedmodel._fitparameters, start_parameters)

def test_compartmentModel_fit_model_determines_right_parameters(lungaif_onec):
    """ Are the fitted parameters the same as the initial parameters?
    This might become a longer test case...
    """

    start_parameters=lungaif_onec._fitparameters
    return_value = lungaif_onec.fit_model()
    print lungaif_onec.OptimizeResult
    assert lungaif_onec._fitted
    #assert np.allclose(lungaif_onec._fitparameters, start_parameters)


def test_compartmentmodels_bootstrapping_output_dimension_and_type(lungaif_onec):
    """ Is the dimension of the bootstrap_result equal to (2,k) 
    and the dimension of mean.- /std.bootstrap_result equal to (2,)?
    Is the output of type dict?
    Does the output dict contain 7 elements?
    Are 'low estimate', 'mean estimate' and 'high estimate' subdicts in the output dict?
    """
    lungaif_onec.k=100   
    fit_result= lungaif_onec.fit_model()
    bootstrap = lungaif_onec.bootstrap()
    assert (lungaif_onec._bootstrapped == True)
    assert (lungaif_onec.bootstrap_result.shape == (3,100))    
    assert (type(lungaif_onec.phys_parameters) == dict)
    assert (len(lungaif_onec.phys_parameters) == 7)   
    assert ('low estimate' and 'high estimate' and 'mean estimate' in 
            lungaif_onec.phys_parameters)
    assert (type(lungaif_onec.phys_parameters['low estimate']) == dict and 
            type(lungaif_onec.phys_parameters['mean estimate']) == dict and
            type(lungaif_onec.phys_parameters['high estimate']) == dict)


def test_compartmentmodels_bootstrapping_output_content(lungaif_onec):    
    """Is 'low estimate' < 'mean estimate' < 'high estimate'?
    Are fitted Parameters in between 'low estimate' and 'high estimate'?
    """
    lungaif_onec.k=100 
    fit_result= lungaif_onec.fit_model()
    bootstrap = lungaif_onec.bootstrap()
    assert (lungaif_onec.bootstrap_result.shape ==(3, lungaif_onec.k))
    assert (lungaif_onec._bootstrapped == True)
    dict_fit={'F':lungaif_onec.phys_parameters['F'],
                'v':lungaif_onec.phys_parameters['v'],
                'MTT':lungaif_onec.phys_parameters['MTT']
                }
    assert (lungaif_onec.phys_parameters['low estimate'] <
            lungaif_onec.phys_parameters['mean estimate'])
    assert (lungaif_onec.phys_parameters['mean estimate'] <
            lungaif_onec.phys_parameters['high estimate'])
    assert (lungaif_onec.phys_parameters['low estimate'] < dict_fit)
    assert (dict_fit < lungaif_onec.phys_parameters['high estimate'])
 
     
def test_compartmentmodels_bootstrapping_output_content_brainaif_onec(brainaif_onec):    
    """Is 'low estimate' < 'mean estimate' < 'high estimate'?
    We investigate a cerebral aif here.
    
    Are fitted Parameters in between 'low estimate' and 'high estimate'?
    """
    fit_result= brainaif_onec.fit_model()
    bootstrap = brainaif_onec.bootstrap()
    assert (brainaif_onec._bootstrapped == True)
    dict_fit={'F':brainaif_onec.phys_parameters['F'],
                'v':brainaif_onec.phys_parameters['v'],
                'MTT':brainaif_onec.phys_parameters['MTT']
                }
    assert (brainaif_onec.phys_parameters['low estimate'] <
            brainaif_onec.phys_parameters['mean estimate'])
    assert (brainaif_onec.phys_parameters['mean estimate'] <
            brainaif_onec.phys_parameters['high estimate'])
    assert (brainaif_onec.phys_parameters['low estimate'] < dict_fit)
    assert (dict_fit < brainaif_onec.phys_parameters['high estimate'])
    
def test_AIC_higher_for_complex_models():
    """ in a one-compartment-situation, a model with more than one compartment  should have a higher AIC value
    """
    from compartmentmodels.compartmentmodels import TwoCXModel, TwoCUModel, CompartmentModel
    from compartmentmodels.compartmentmodels import loaddata
    
    startdict = {'F': 31.0, 'v': 4.2}

    time, aif1, aif2 =loaddata(filename='tests/cerebralartery.csv')    
    # remove baseline signal
    aif = aif1 - aif1[0:5].mean()
    ocm = CompartmentModel(
        time=time, curve=aif, aif=aif, startdict={'F': 31.0, 'v': 4.2})
    # calculate a model curve
    ocm.curve = ocm.calc_modelfunction(ocm._fitparameters)
    ocm.curve += 0.02 * ocm.curve.max() * np.random.randn(len(time))
    
    ocm.fit_model()
    aic_1c=ocm.get_AIC()


    twocxm = TwoCXModel(
        time=time, curve=ocm.curve, aif=aif, startdict={'Fp': 31.0, 'vp': 4.2, 'PS':0.001, 've':11.2})
    twocxm.fit_model()
    aic_2cx = twocxm.get_AIC()

    twocum = TwoCUModel(
        time=time, curve=ocm.curve, aif=aif, startdict={'Fp': 31.0, 'vp': 4.2, 'PS':0.001, 've':11.2})
    twocum.fit_model()
    aic_2cu = twocum.get_AIC()
    assert (aic_1c < aic_2cx)
    assert (aic_1c < aic_2cu)
    assert (aic_2cu < aic_2cx)

    
def test_compartmentmodel_cython_convolution_equal_to_python(preparedmodel):
    """ Does the cython convolution yield the same result as the python implementation?

    And how much faster ist is, anyway?
    """
    original_curve = preparedmodel.curve

    preparedmodel._use_cython=True

    curve = preparedmodel.calc_modelfunction(preparedmodel._fitparameters)

    assert np.allclose(original_curve, curve)
    
    
def test_compartmentmodel_cython_is_faster_than_python(preparedmodel):
    """ Is the cython implementation faster than the python implementation? """

    # to do: how do we get the execution time=?
    preparedmodel._use_cython=False

    pythontime= timeit.timeit(lambda:preparedmodel.calc_modelfunction(preparedmodel._fitparameters), number = 1000)
    preparedmodel._use_cython=True
    cythontime= timeit.timeit(lambda:preparedmodel.calc_modelfunction(preparedmodel._fitparameters), number=1000)
    print "Python:  {}; Cython: {}".format(pythontime, cythontime)
    assert cythontime<pythontime

