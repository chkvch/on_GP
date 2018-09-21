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

    def get_logrho_h(self, lgp, lgt):
        return rbs(self.logpvals, self.logtvals, self.logrho, **self.spline_kwargs)(lgp, lgt, grid=False)
    def get_logs_h(self, lgp, lgt):
        return rbs(self.logpvals, self.logtvals, self.logs, **self.spline_kwargs)(lgp, lgt, grid=False)
    def get_sp_h(self, lgp, lgt):
        return rbs(self.logpvals, self.logtvals, self.logs, **self.spline_kwargs)(lgp, lgt, grid=False, dx=1)
    def get_st_h(self, lgp, lgt):
        return rbs(self.logpvals, self.logtvals, self.logs, **self.spline_kwargs)(lgp, lgt, grid=False, dy=1)

    def get_logrho_he(self, lgp, lgt):
        return self.he_eos.get_he_logrho((lgp, lgt))
    def get_logs_he(self, lgp, lgt):
        return self.he_eos.get_he_logs((lgp, lgt))
    def get_sp_he(self, lgp, lgt):
        return self.he_eos.get_he_sp((lgp, lgt))
    def get_st_he(self, lgp, lgt):
        return self.he_eos.get_he_st((lgp, lgt))

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

        rhoinv = y / 10 ** self.get_logrho_he(logp, logt) + (1. - y) / 10 ** self.get_logrho_h(logp, logt)
        logrho = np.log10(rhoinv ** -1.)

        return {'grada':grada, 'logrho':logrho, 'logs':np.log10(s)}

    def get_grada(self, logp, logt, y):
        return self.get(logp, logt, y)['grada']

    def get_logrho(self, logp, logt, y):
        return self.get(logp, logt, y)['logrho']

    def get_logs(self, logp, logt, y):
        return self.get(logp, logt, y)['logs']
