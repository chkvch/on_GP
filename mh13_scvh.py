from scipy.interpolate import RectBivariateSpline as rbs
import scvh
import numpy as np

class eos:
    def __init__(self, path_to_data):
        self.columns = 'logp', 'logt', 'logrho', 'logs'
        self.h_path = '{}/MH13+SCvH-H-2018.dat'.format(path_to_data)
        self.h_data = np.genfromtxt(self.h_path, skip_header=16, names=self.columns)

        self.logpvals = np.unique(self.h_data['logp'][self.h_data['logp'] <= 14.])
        self.logtvals = np.unique(self.h_data['logt'][self.h_data['logp'] <= 14.])

        self.logrho = np.zeros((len(self.logpvals), len(self.logtvals)))
        self.logs = np.zeros((len(self.logpvals), len(self.logtvals)))
        for i, logpval in enumerate(self.logpvals):
            self.logrho[i] = self.h_data['logrho'][self.h_data['logp'] == logpval]
            self.logs[i] = self.h_data['logs'][self.h_data['logp'] == logpval]

            # class scipy.interpolate.RectBivariateSpline(x, y, z, bbox=[None, None, None, None], kx=3, ky=3, s=0)
            #     Bivariate spline approximation over a rectangular mesh.

            #     Can be used for both smoothing and interpolating data.

            #     x,y : array_like
            #     1-D arrays of coordinates in strictly ascending order.

            #     z : array_like
            #     2-D array of data with shape (x.size,y.size).

            #     bbox : array_like, optional
            #     Sequence of length 4 specifying the boundary of the rectangular approximation domain. By default, bbox=[min(x,tx),max(x,tx), min(y,ty),max(y,ty)].

            #     kx, ky : ints, optional
            #     Degrees of the bivariate spline. Default is 3.

            #     s : float, optional
            #     Positive smoothing factor defined for estimation condition: sum((w[i]*(z[i]-s(x[i], y[i])))**2, axis=0) <= s Default is s=0, which is for interpolation.

        self.spline_kwargs = {'kx':3, 'ky':3}
        self.he_eos = scvh.eos(path_to_data)

    # methods for getting pure hydrogen quantities by interpolating in mh13
    def get_logrho_h(self, lgp, lgt):
        return rbs(self.logpvals, self.logtvals, self.logrho, **self.spline_kwargs)(lgp, lgt, grid=False)
    def get_logs_h(self, lgp, lgt):
        return rbs(self.logpvals, self.logtvals, self.logs, **self.spline_kwargs)(lgp, lgt, grid=False)
    def get_sp_h(self, lgp, lgt):
        return rbs(self.logpvals, self.logtvals, self.logs, **self.spline_kwargs)(lgp, lgt, grid=False, dx=1)
    def get_st_h(self, lgp, lgt):
        return rbs(self.logpvals, self.logtvals, self.logs, **self.spline_kwargs)(lgp, lgt, grid=False, dy=1)
    # def get_rhop_h(self, lgp, lgt):
    #     return rbs(self.logpvals, self.logtvals, self.logrho, **self.spline_kwargs)(lgp, lgt, grid=False, dx=1)
    # def get_rhot_h(self, lgp, lgt):
    #     return rbs(self.logpvals, self.logtvals, self.logrho, **self.spline_kwargs)(lgp, lgt, grid=False, dy=1)
    # rho_t and rho_p from MH13 tables are presenting some difficulties, e.g., rhot_h changes sign in the neighborhood of
    # 1 Mbar in a Jupiter adiabat. instead get rhot_h and rhop_h from the scvh tables below. only really enters
    # the calculation of brunt_B.

    # methods for getting pure helium quantities by interpolating in scvh
    def get_logrho_he(self, lgp, lgt):
        return self.he_eos.get_he['logrho'](lgp, lgt, grid=False)
    def get_logs_he(self, lgp, lgt):
        return self.he_eos.get_he['logs'](lgp, lgt, grid=False)
    def get_sp_he(self, lgp, lgt):
        return self.he_eos.get_he['sp'](lgp, lgt, grid=False)
    def get_st_he(self, lgp, lgt):
        return self.he_eos.get_he['st'](lgp, lgt, grid=False)
    def get_rhop_he(self, lgp, lgt):
        return self.he_eos.get_he['rhop'](lgp, lgt, grid=False)
    def get_rhot_he(self, lgp, lgt):
        return self.he_eos.get_he['rhot'](lgp, lgt, grid=False)
    def get_rhop_h(self, lgp, lgt):
        return self.he_eos.get_h['rhop'](lgp, lgt, grid=False)
    def get_rhot_h(self, lgp, lgt):
        return self.he_eos.get_h['rhot'](lgp, lgt, grid=False)

    # general method for getting quantities for hydrogen-helium mixture
    def get(self, logp, logt, y):
        s_h = 10 ** self.get_logs_h(logp, logt)
        s_he = 10 ** self.get_logs_he(logp, logt)
        sp_h = self.get_sp_h(logp, logt)
        st_h = self.get_st_h(logp, logt)
        sp_he = self.get_sp_he(logp, logt)
        st_he = self.get_st_he(logp, logt)

        s = (1. - y) * s_h + y * s_he # + smix
        st = (1. - y) * s_h / s * st_h + y * s_he / s * st_he # + smix/s*dlogsmix/dlogt
        sp = (1. - y) * s_h / s * sp_h + y * s_he / s * sp_he # + smix/s*dlogsmix/dlogp
        grada = - sp / st

        rho_h = 10 ** self.get_logrho_h(logp, logt)
        rho_he = 10 ** self.get_logrho_he(logp, logt)
        rhoinv = y / rho_he + (1. - y) / rho_h
        rho = rhoinv ** -1.
        logrho = np.log10(rho)
        rhop_h = self.get_rhop_h(logp, logt)
        rhot_h = self.get_rhot_h(logp, logt)
        rhop_he = self.get_rhop_he(logp, logt)
        rhot_he = self.get_rhot_he(logp, logt)

        rhot = (1. - y) * rho / rho_h * rhot_h + y * rho / rho_he * rhot_he
        rhop = (1. - y) * rho / rho_h * rhop_h + y * rho / rho_he * rhop_he

        chirho = 1. / rhop # dlnP/dlnrho|T
        chit = -1. * rhot / rhop # dlnP/dlnT|rho
        gamma1 = 1. / (sp ** 2 / st + rhop) # dlnP/dlnrho|s
        chiy = -1. * rho * y * (1. / rho_he - 1. / rho_h) # dlnrho/dlnY|P,T

        res =  {
            'grada':grada,
            'logrho':logrho,
            'logs':np.log10(s),
            'gamma1':gamma1,
            'chirho':chirho,
            'chit':chit,
            'gamma1':gamma1,
            'chiy':chiy,
            'rho_h':rho_h,
            'rho_he':rho_he,
            'rhop':rhop,
            'rhot':rhot
            }
        return res

    def get_grada(self, logp, logt, y):
        return self.get(logp, logt, y)['grada']

    def get_logrho(self, logp, logt, y):
        return self.get(logp, logt, y)['logrho']

    def get_logs(self, logp, logt, y):
        return self.get(logp, logt, y)['logs']

    def get_gamma1(self, logp, logt, y):
        return self.get(logp, logt, y)['gamma1']

    # def get_chiy(self, logp, logt, y):
    #     """dlogrho/dlogY at const p, t"""
    #
    #     f = self.fac_for_numerical_partials
    #
    #     y_lo = y * (1. - f)
    #     y_hi = y * (1. + f)
    #     if np.any(y_lo < 0.) or np.any(y_hi > 1.):
    #         print('warning: chiy not calculable for y this close to 0 or 1. should change size of step for finite differences.')
    #         return None
    #
    #     # logrho = self.get_logrho(logp, logt, y)
    #     # logp_lo = self.rhot_get(logrho, logt, y_lo)['logp']
    #     # logp_hi = self.rhot_get(logrho, logt, y_hi)['logp']
    #
    #     # return (logp_hi - logp_lo) / 2. / f
    #
    #     logrho_lo = self.get_logrho(logp, logt, y_lo)
    #     logrho_hi = self.get_logrho(logp, logt, y_hi)
    #     return (logrho_hi  - logrho_lo) / 2. / f
