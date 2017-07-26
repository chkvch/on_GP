import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import RegularGridInterpolator

class eos:
    
    def __init__(self):
        path = '/Users/chris/Dropbox/planet_models/reos/reos_water_pt.dat'
        
        # Nadine 22 Sep 2015: Fifth column is entropy in kJ/g/K+offset

        self.names = 'logrho', 'logt', 'logp', 'logu', 'logs', 'chit', 'chirho', 'gamma1'
        self.data = np.genfromtxt(path, names=self.names)

        self.logpvals = np.unique(self.data['logp'])
        self.logtvals = np.unique(self.data['logt'])
        
        self.logpmin = min(self.logpvals)
        self.logpmax = max(self.logpvals)
        self.logtmin = min(self.logtvals)
        self.logtmax = max(self.logtvals)
                
        self.nptsp = len(self.logpvals)
        self.nptst = len(self.logtvals)
        
        self.logrho_on_pt = np.zeros((self.nptsp, self.nptst))
        self.logu_on_pt = np.zeros((self.nptsp, self.nptst))
        self.logs_on_pt = np.zeros((self.nptsp, self.nptst))
        self.chit_on_pt = np.zeros((self.nptsp, self.nptst))
        self.chirho_on_pt = np.zeros((self.nptsp, self.nptst))
        self.gamma1_on_pt = np.zeros((self.nptsp, self.nptst))

        for i, logpval in enumerate(self.logpvals):
            data_this_logp = self.data[self.data['logp'] == logpval]
            for j, logtval in enumerate(self.logtvals):
                data_this_logp_logt = data_this_logp[data_this_logp['logt'] == logtval]
                self.logrho_on_pt[i, j] = data_this_logp_logt['logrho']
                self.logu_on_pt[i, j] = data_this_logp_logt['logu']
                self.logs_on_pt[i, j] = data_this_logp_logt['logs']
                self.chit_on_pt[i, j] = data_this_logp_logt['chit']
                self.chirho_on_pt[i, j] = data_this_logp_logt['chirho']
                self.gamma1_on_pt[i, j] = data_this_logp_logt['gamma1']

        pt_basis = (self.logpvals, self.logtvals)
        self._get_logrho = RegularGridInterpolator(pt_basis, self.logrho_on_pt, bounds_error=False)
        self._get_logu = RegularGridInterpolator(pt_basis, self.logu_on_pt)
        self._get_logs = RegularGridInterpolator(pt_basis, self.logs_on_pt)        
        self._get_chit = RegularGridInterpolator(pt_basis, self.chit_on_pt)        
        self._get_chirho = RegularGridInterpolator(pt_basis, self.chirho_on_pt)        
        self._get_gamma1 = RegularGridInterpolator(pt_basis, self.gamma1_on_pt)        
                
    def get_logrho(self, logp, logt):        
        return self._get_logrho((logp, logt))

    def get_logu(self, logp, logt):
        return self._get_logu((logp, logt))

    def get_logs(self, logp, logt):
        return self._get_logs((logp, logt)) # + 10. # kJ/g/K to erg/g/K
        
    def get_chit(self, logp, logt):
        return self._get_chit((logp, logt))

    def get_chirho(self, logp, logt):
        return self._get_chirho((logp, logt))

    def get_gamma1(self, logp, logt):
        return self._get_gamma1((logp, logt))
                
    def get_dlogrho_dlogp_const_t(self, logp, logt, f=1e-1):
        logp_lo = logp - np.log10(1. - f)
        logp_hi = logp + np.log10(1. + f)
        logrho_lo = self.get_logrho(logp_lo, logt)
        logrho_hi = self.get_logrho(logp_hi, logt)
        return (logrho_hi - logrho_lo) / (logp_hi - logp_lo)

    def get_dlogrho_dlogt_const_p(self, logp, logt, f=1e-1):
        logt_lo = logt + np.log10(1. - f)
        logt_hi = logt + np.log10(1. + f)
        logrho_lo = self.get_logrho(logp, logt_lo)
        logrho_hi = self.get_logrho(logp, logt_hi)
        return (logrho_hi - logrho_lo) / (logt_hi - logt_lo)

    def get_dlogs_dlogp_const_t(self, logp, logt, f=1e-1):
        logp_lo = logp - np.log10(1. - f)
        logp_hi = logp + np.log10(1. + f)
        logs_lo = self.get_logs(logp_lo, logt)
        logs_hi = self.get_logs(logp_hi, logt)
        return (logs_hi - logs_lo) / (logp_hi - logp_lo)

    def get_dlogs_dlogt_const_p(self, logp, logt, f=1e-1):
        logt_lo = logt - np.log10(1. - f)
        logt_hi = logt + np.log10(1. + f)
        logs_lo = self.get_logs(logp, logt_lo)
        logs_hi = self.get_logs(logp, logt_hi)
        return (logs_hi - logs_lo) / (logt_hi - logt_lo)
        
    def get_cp(self, logp, logt):
        rhop = self.get_dlogrho_dlogp_const_t(logp, logt)
        rhot = self.get_dlogrho_dlogt_const_p(logp, logt)
        rho = 10 ** self.get_logrho(logp, logt)
        sp = self.get_dlogs_dlogp_const_t(logp, logt)
        st = self.get_dlogs_dlogt_const_p(logp, logt)
        s = 10 ** self.get_logs(logp, logt)
        dpdt_const_rho = - 10 ** logp / 10 ** logt * rhot / rhop
        dudt_const_rho = s * (st - sp * rhot / rhop)
        dpdu_const_rho = dpdt_const_rho / rho / dudt_const_rho
        gamma3 = 1. + dpdu_const_rho # cox and giuli 9.93a
        gamma1 = self.get_gamma1(logp, logt) # (gamma3 - 1.) / res['grada']
        chirho = rhop ** -1
        chit = dpdt_const_rho * 10 ** logt / 10 ** logp
        cv = chit * 10 ** logp / (rho * 10 ** logt * (gamma3 - 1.))
        cp = cv + 10 ** logp * chit ** 2 / (rho * 10 ** logt * chirho)
        # print 'rhop, rhot, rho', rhop, rhot, rho
        # print 'sp, st, s', sp, st, s
        # print 'dpdt, dudt, dpdu const rho', dpdt_const_rho, dudt_const_rho, dpdu_const_rho
        # print 'gamma3, gamma1, chirho, chit', gamma3, gamma1, chirho, chit
        # print 'cp, cv', cp, cv
        # print
        return cp

    # def get_dlogrho_dlogt_const_p(self, logp, logt):
    #     return self.get_chit(logp, logt) / self.get_chirho(logp, logt)
    #
    # def get_dlogrho_dlogp_const_t(self, logp, logt):
    #     return 1. / self.get_chirho(logp, logt)


        
    # def get_gamma1(self, logp, logt, f=5e-1):
    #     '''take centered differences to compute dlogp/dlogrho at constant entropy.
    #     uses the version of this module that takes rho, s as the thermodynamic basis.'''
    #     logrho = self.get_logrho(logp, logt)
    #     logs = self.get_logs(logp, logt)
    #     import reos_rhos
    #     rhos_eos = reos_rhos.eos()
    #
    #     logrho_hi = logrho + np.log10(1. + f)
    #     logrho_lo = logrho + np.log10(1. - f)
    #     logp_hi = rhos_eos.get_logp(logrho_hi, logs)
    #     logp_lo = rhos_eos.get_logp(logrho_lo, logs)
    #
    #     return (logp_hi - logp_lo) / (logrho_hi - logrho_lo)
    #