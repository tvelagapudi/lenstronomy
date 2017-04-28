__author__ = 'sibirrer'

#file which contains class for lens model routines
import numpy as np

class LensModel(object):

    def __init__(self, kwargs_options):
        self.func_list = []
        model_list = kwargs_options['lens_model_list']
        from astrofunc.LensingProfiles.external_shear import ExternalShear
        self.shear = ExternalShear()
        for lens_type in model_list:
            if lens_type == 'EXTERNAL_SHEAR':
                from astrofunc.LensingProfiles.external_shear import ExternalShear
                self.func_list.append(ExternalShear())
            elif lens_type == 'GAUSSIAN':
                from astrofunc.LensingProfiles.gaussian import Gaussian
                self.func_list.append(Gaussian())
            elif lens_type == 'SIS':
                from astrofunc.LensingProfiles.sis import SIS
                self.func_list.append(SIS())
            elif lens_type == 'SIS_TRUNCATED':
                from astrofunc.LensingProfiles.sis_truncate import SIS_truncate
                self.func_list.append(SIS_truncate())
            elif lens_type == 'SPP':
                from astrofunc.LensingProfiles.spp import SPP
                self.func_list.append(SPP())
            elif lens_type == 'SPEP':
                from astrofunc.LensingProfiles.spep import SPEP
                self.func_list.append(SPEP())
            elif lens_type == 'SPEMD':
                from astrofunc.LensingProfiles.spemd import SPEMD
                self.func_list.append(SPEMD())
            elif kwargs_options['lens_type'] == 'NFW':
                from astrofunc.LensingProfiles.nfw import NFW
                self.func_list.append(NFW())
            elif kwargs_options['lens_type'] == 'INTERPOL':
                from astrofunc.LensingProfiles.interpol import Interpol_func
                self.func_list.append(Interpol_func())
            elif kwargs_options['lens_type'] == 'SHAPELETS_POLAR':
                from astrofunc.LensingProfiles.shapelet_pot import PolarShapelets
                self.func_list.append(PolarShapelets())
            elif kwargs_options['lens_type'] == 'SHAPELETS_CART':
                from astrofunc.LensingProfiles.shapelet_pot_2 import CartShapelets
                self.func_list.append(CartShapelets())
            elif kwargs_options['lens_type'] == 'DIPOLE':
                from astrofunc.LensingProfiles.dipole import Dipole
                self.func_list.append(Dipole())
            elif kwargs_options['lens_type'] == 'NONE':
                from astrofunc.LensingProfiles.no_lens import NoLens
                self.func_list.append(NoLens())
            else:
                raise ValueError('options do not include a valid lens model!', kwargs_options['lens_type'])
        self.foreground_shear = kwargs_options.get('foreground_shear', False)

        self.perturb_alpha = kwargs_options.get("perturb_alpha", False)
        if self.perturb_alpha:
            self.alpha_perturb_x = kwargs_options["alpha_perturb_x"]
            self.alpha_perturb_y = kwargs_options["alpha_perturb_y"]

    def mass(self, x, y, sigma_crit, kwargs):
        kappa = self.kappa(x, y, kwargs)
        mass = sigma_crit*kappa
        return mass

    def potential(self, x, y, kwargs, kwargs_else=None):
        if self.foreground_shear:
            f_x_shear1, f_y_shear1 = self.shear.derivatives(x, y, e1=kwargs_else['gamma1_foreground'], e2=kwargs_else['gamma2_foreground'])
            x_ = x - f_x_shear1
            y_ = y - f_y_shear1
        else:
            x_ = x
            y_ = y
        potential = np.zeros_like(x)
        for i, func in enumerate(self.func_list):
            potential += func.function(x_, y_, **kwargs[i])
        return potential

    def alpha(self, x, y, kwargs, kwargs_else=None):
        """
        a = grad(phi)
        """
        if self.foreground_shear:
            f_x_shear1, f_y_shear1 = self.shear.derivatives(x, y, e1=kwargs_else['gamma1_foreground'], e2=kwargs_else['gamma2_foreground'])
            x_ = x - f_x_shear1
            y_ = y - f_y_shear1
        else:
            x_ = x
            y_ = y
        f_x, f_y = np.zeros_like(x_), np.zeros_like(x_)
        for i, func in enumerate(self.func_list):
            f_x_i, f_y_i = func.derivatives(x_, y_, **kwargs[i])
            f_x += f_x_i
            f_y += f_y_i
        if self.perturb_alpha:
            f_x += self.alpha_perturb_x
            f_y += self.alpha_perturb_y
        return f_x, f_y

    def kappa(self, x, y, kwargs, kwargs_else=None):
        """
        k = 1/2 laplacian(phi)
        """
        f_xx, f_xy, f_yy = self.hessian(x, y, kwargs, kwargs_else=kwargs_else)
        kappa = 1./2 * (f_xx + f_yy)  # attention on units
        return kappa

    def gamma(self, x, y, kwargs, kwargs_else=None):
        """
        g1 = 1/2(d^2phi/dx^2 - d^2phi/dy^2)
        g2 = d^2phi/dxdy
        """
        f_xx, f_xy, f_yy = self.hessian(x, y, kwargs, kwargs_else=kwargs_else)
        gamma1 = 1./2 * (f_xx - f_yy)  # attention on units
        gamma2 = f_xy  # attention on units
        return gamma1, gamma2

    def magnification(self, x, y, kwargs, kwargs_else=None):
        """
        mag = 1/det(A)
        A = 1 - d^2phi/d_ij
        """
        f_xx, f_xy, f_yy = self.hessian(x, y, kwargs, kwargs_else=kwargs_else)
        det_A = (1 - f_xx) * (1 - f_yy) - f_xy*f_xy  # attention, only works in right units of critical density
        return 1./det_A  # attention, if dividing to zero

    def all(self, x, y, kwargs, kwargs_else=None):
        """
        specially build to reduce computational costs
        """
        if self.foreground_shear:
            f_x_shear1, f_y_shear1 = self.shear.derivatives(x, y, e1=kwargs_else['gamma1_foreground'],
                                                            e2=kwargs_else['gamma2_foreground'])
            x_ = x - f_x_shear1
            y_ = y - f_y_shear1
        else:
            x_ = x
            y_ = y
        potential = np.zeros_like(x)
        f_x, f_y = np.zeros_like(x_), np.zeros_like(x_)
        f_xx, f_yy, f_xy = np.zeros_like(x_), np.zeros_like(x_), np.zeros_like(x_)
        for func in self.func_list:
            potential += func.function(x_, y_, **kwargs)
            f_x_i, f_y_i = func.derivatives(x_, y_, **kwargs)
            f_x += f_x_i
            f_y += f_y_i
            f_xx_i, f_yy_i, f_xy_i = func.hessian(x_, y_, **kwargs)
            f_xx += f_xx_i
            f_yy += f_yy_i
            f_xy += f_xy_i
        kappa = 1./2 * (f_xx + f_yy)  # attention on units
        gamma1 = 1./2 * (f_xx - f_yy)  # attention on units
        gamma2 = f_xy  # attention on units
        det_A = (1 - f_xx) * (1 - f_yy) - f_xy*f_xy  # attention, only works in right units of critical density
        mag = 1./det_A
        return potential, f_x, f_y, kappa, gamma1, gamma2, mag

    def hessian(self, x, y, kwargs, kwargs_else=None):

        # TODO non-linear part of foreground shear is not computed! Use numerical estimate or chain rule!

        if self.foreground_shear:
            f_x_shear1, f_y_shear1 = self.shear.derivatives(x, y, e1=kwargs_else['gamma1_foreground'],
                                                            e2=kwargs_else['gamma2_foreground'])
            x_ = x - f_x_shear1
            y_ = y - f_y_shear1
        else:
            x_ = x
            y_ = y
        f_xx, f_yy, f_xy = np.zeros_like(x_), np.zeros_like(x_), np.zeros_like(x_)
        for i, func in enumerate(self.func_list):
            f_xx_i, f_yy_i, f_xy_i = func.hessian(x_, y_, **kwargs[i])
            f_xx += f_xx_i
            f_yy += f_yy_i
            f_xy += f_xy_i
        return f_xx, f_xy, f_yy