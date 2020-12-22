import numpy as np
from . import norm_lens
from . import norm_src
from . import norm_tau
from . import norm_rot


est_list = ['TT','TE','EE','EB','TB','MV','MVPOL','SRC','MASK','TAU','ROT','SRC_X_TT']



def get_norms(estimators,response_cls,total_cls,lmin,lmax,k_ellmax=None,
              include_bb_mv=False,no_corr=True):
    """
    Get norms for estimators such that A_est = N_est. In the case of lensing,
    this corresponds to the normalizations of the lensing potential.
    
    Args:
        estimator (str): A string belonging to one of ['TT','TE','EE','EB',
    'TB','MV','MVPOL','src','mask','tau','rot']

        response_cls (dict): A dictionary mapping strings TT,EE,TE to 1d numpy 
    arrays containing the noiseless power spectra used in the lensing response.
    For unbiased results, lensed spectra are recommended for EE and TE, and
    the gradient cross-spectrum for TT. The array elements should correspond to 
    multipoles 0,1,2,...,lmax.

        total_cls (dict): A dictionary mapping strings TT,EE,TE,BB to 1d numpy 
    arrays containing the total power spectra assumed in the filters.
    The array elements should correspond to multipoles 0,1,2,...,lmax.

        lmin (int): The minimum multipole to be used.
        lmax (int): The maximum multipole to be used.
        k_ellmax (optional,int): The maximum multipole in the output noise curve.
    Defaults to lmax.
    """
    ests = [e.upper() for e in estimators]
    assert [est in est_list for est in ests], 'Unrecognized estimator.'
    if k_ellmax is None: k_ellmax = lmax
    ucl = response_cls
    tcl = total_cls
    Tcmb  = 2.726e6 # CMB temperature assumed in tempura

    def _gk(e): # get key
        return estimators[ests.index(e)]
    
    res = {}
    if ('TT' in ests) or (('MV' in ests) and no_corr):
        r_tt = np.asarray(norm_lens.qtt(k_ellmax,lmin,lmax,ucl['TT'],tcl['TT'],gtype='')) 
        if ('TT' in ests): res[_gk('TT')] = r_tt
    if ('EE' in ests) or ('MVPOL' in ests) or (('MV' in ests) and no_corr):
        r_ee = np.asarray(norm_lens.qee(k_ellmax,lmin,lmax,ucl['EE'],tcl['EE'],gtype= ''))
        if ('EE' in ests): res[_gk('EE')] = r_ee
    if ('EB' in ests) or ('MVPOL' in ests) or (('MV' in ests) and no_corr):
        r_eb = np.asarray(norm_lens.qeb(k_ellmax,lmin,lmax,ucl['EE'],tcl['EE'],tcl['BB'],gtype= ''))
        if ('EB' in ests): res[_gk('EB')] = r_eb
    if ('TE' in ests)  or (('MV' in ests) and no_corr):
        r_te = np.asarray(norm_lens.qte(k_ellmax,lmin,lmax,ucl['TE'],tcl['TT'],tcl['EE'],gtype= ''))
        if ('TE' in ests): res[_gk('TE')] = r_te
    if ('TB' in ests) or  (('MV' in ests) and no_corr):
        r_tb = np.asarray(norm_lens.qtb(k_ellmax,lmin,lmax,ucl['TE'],tcl['TT'],tcl['BB'],gtype= ''))
        if ('TB' in ests): res[_gk('TB')] = r_tb
    if 'MV' in ests:
        if no_corr:
            r_mv = r_tt * 0
            # Take 1/N coadd of EE and EB
            # gradient is non-zero for ell>=1
            # curl is non-zero for ell>=2
            r_mv[0,1:] = 1./ sum([1./x[0,1:] for x in [r_tt,r_te,r_ee,r_eb,r_tb]])
            r_mv[1,2:] = 1./ sum([1./x[1,2:] for x in [r_tt,r_te,r_ee,r_eb,r_tb]])
            res[_gk('MV')] = r_mv
        else:
            fC = np.asarray((ucl['TT'],ucl['EE'],ucl['BB'],ucl['TE']))
            OC = np.asarray((tcl['TT'],tcl['EE'],tcl['BB'],tcl['TE']))
            Ag,Ac,Wg,Wc = norm_lens.qall([True,True,True,True,True,include_bb_mv],k_ellmax,lmin,lmax,fC,OC,gtype= '')
            res[_gk('MV')] = np.asarray((Ag[-1,:],Ac[-1,:]))
    if 'MVPOL' in ests:
        r_mvpol = r_ee * 0
        # Take 1/N coadd of EE and EB
        # gradient is non-zero for ell>=1
        # curl is non-zero for ell>=2
        r_mvpol[0,1:] = 1./(1./r_ee[0,1:] + 1./r_eb[0,1:])
        r_mvpol[1,2:] = 1./(1./r_ee[1,2:] + 1./r_eb[1,2:])
        res[_gk('MVPOL')] = r_mvpol
    if 'MASK' in ests:
        raise NotImplementedError
    if 'SRC' in ests:
        res[_gk('SRC')] = norm_src.qtt(k_ellmax,lmin,lmax,tcl['TT'])
    if 'ROT' in ests:
        raise NotImplementedError # Just haven't gotten around to interfacing this
    if 'TAU' in ests:
        raise NotImplementedError # Just haven't gotten around to interfacing this
    if 'SRC_X_TT' in ests:
        res[_gk('SRC_X_TT')] = norm_lens.stt(k_ellmax,lmin,lmax,ucl['TT'],tcl['TT'],gtype= '')

    return res
    

    
