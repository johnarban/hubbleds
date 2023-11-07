from astropy import units as u
from astropy.modeling import models, fitting
from numpy import pi

try:
    from astropy.cosmology import Planck18 as planck
except ImportError:
    from astropy.cosmology import Planck15 as planck

__all__ = [
    'HUBBLE_ROUTE_PATH',
    'MILKY_WAY_SIZE_MPC', 'H_ALPHA_REST_LAMBDA',
    'MG_REST_LAMBDA', 'GALAXY_FOV', 'FULL_FOV',
    'angle_to_json', 'angle_from_json',
    'age_in_gyr', 'format_fov', 'format_measured_angle',
]

HUBBLE_ROUTE_PATH = "hubbles_law"

MILKY_WAY_SIZE_LTYR = 100000 * u.lightyear
MILKY_WAY_SIZE_MPC = MILKY_WAY_SIZE_LTYR.to(u.Mpc).value
DISTANCE_CONSTANT = round(
    MILKY_WAY_SIZE_MPC * 3600 * 180 / pi / 100) * 100  # theta = L/D:  Distance in Mpc = DISTANCE_CONSTANT / theta in arcsec; Round to hundreds to match slideshow notes.

AGE_CONSTANT = round( 1.e6 * u.pc.to(u.km)/ (1e9 * u.yr.to(u.s)) / 10  ) * 10 # t = d/v
HST_KEY_AGE = 12.79687910  # (1/H_0) in Gyr

SPEED_OF_LIGHT = 3.0 * 10 ** 5 # km/s
# Both in angstroms
H_ALPHA_REST_LAMBDA = 6565  # SDSS calibrates to wavelengths in a vacuum
MG_REST_LAMBDA = 5172  # The value used by SDSS is actually 5176.7, but that wavelength aligns with an upward bump, so we are adjusting it to 5172 to avoid confusing students. Ziegler & Bender 1997 uses lambda_0 ~ 5170, so our choice is justifiable.

GALAXY_FOV = 1.5 * u.arcmin
FULL_FOV = 60 * u.deg

IMAGE_BASE_URL = "https://cosmicds.github.io/cds-website/hubbleds_images"


def angle_to_json(angle, _widget):
    return {
        "value": angle.value,
        "unit": angle.unit.name
    }


def angle_from_json(jsn, _widget):
    return jsn["value"] * u.Unit(jsn["unit"])


def age_in_gyr(H0):
    """
    Given a value for the Hubble constant, computes the age of the universe
    in Gyr, based on the Planck cosmology.

    Parameters
    ----------
    H0: float
        The value of the Hubble constant

    Returns
    ----------
    age: numpy.float64
        The age of the universe, in Gyr
    """
    age = planck.clone(H0=H0).age(0)
    unit = age.unit
    return age.value * unit.to(u.Gyr)


def age_in_gyr_simple(H0):
    inv = 1 / H0
    mpc_to_km = u.Mpc.to(u.km)
    s_to_gyr = u.s.to(u.Gyr)
    return round(inv * mpc_to_km * s_to_gyr, 3)


def fit_line(x, y):
    try:
        fit = fitting.LinearLSQFitter()
        line_init = models.Linear1D(intercept=0, fixed={'intercept': True})
        fitted_line = fit(line_init, x, y)
        return fitted_line
    except ValueError:
        return None


def format_fov(fov, units=True):
    suffix = " (dd:mm:ss)" if units else ""
    return fov.to_string(unit=u.degree, sep=":", precision=0,
                         pad=True) + suffix


def format_measured_angle(angle):
    if angle == 0:
        return ""
    return angle.to_string(unit=u.arcsec, precision=0)[:-6] + " arcseconds"


def velocity_from_wavelengths(lamb_meas, lamb_rest):
    return round((3 * (10 ** 5) * (lamb_meas / lamb_rest - 1)), 0)

def distance_from_angular_size(theta):
    return round(DISTANCE_CONSTANT / theta, 0)
