import astropy.units as u
import ipyvue as v
from astropy.coordinates import SkyCoord
from astropy.table import Table
from cosmicds.utils import API_URL, request_session
from cosmicds.utils import load_template
from ipywidgets import DOMWidget, widget_serialization
from pandas import DataFrame, concat
from pywwt.jupyter import WWTJupyterWidget
from traitlets import Dict, Instance, Int, Bool, observe

from ...utils import FULL_FOV, GALAXY_FOV
from ...utils import HUBBLE_ROUTE_PATH


class SelectionTool(v.VueTemplate):
    template = load_template("selection_tool.vue", __file__,
                             traitlet=True).tag(sync=True)
    widget = Instance(DOMWidget, allow_none=True).tag(sync=True,
                                                      **widget_serialization)
    current_galaxy = Dict().tag(sync=True)
    candidate_galaxy = Dict().tag(sync=True)
    selected_count = Int().tag(sync=True)
    dialog = Bool(False).tag(sync=True)
    flagged = Bool(False).tag(sync=True)
    selected = Bool(False).tag(sync=True)

    UPDATE_TIME = 1  # seconds
    START_COORDINATES = SkyCoord(180 * u.deg, 25 * u.deg, frame='icrs')

    def __init__(self, data, *args, **kwargs):
        self.widget = WWTJupyterWidget(hide_all_chrome=True)
        self.widget.background = 'SDSS: Sloan Digital Sky Survey (Optical)'
        self.widget.foreground = 'SDSS: Sloan Digital Sky Survey (Optical)'
        self.widget.center_on_coordinates(self.START_COORDINATES, fov= 6 * u.arcmin, #start in close enough to see galaxies
                                          instant=False)

        df = data.to_dataframe()
        self.table = Table.from_pandas(df)
        self.motions_left = 2
        self.gals_max = kwargs.get("galaxies_max", 5)
        
        self.sdss_layer = None
        show_galaxy_layer = kwargs.get("show_galaxies", False)
        if show_galaxy_layer:
            self.show_galaxies()

        self.selected_layer = None
        self.selected_data = kwargs.get("selected_data", None)
        if self.selected_data is None:
            self.selected_data = DataFrame()
        if self.selected_data.shape[0] > 0:
            self._create_selected_layer()
        self.current_galaxy = {}
        self.candidate_galaxy = {}
        self._on_galaxy_selected = None

        self._request_session = request_session()

        def wwt_cb(wwt, updated):
            if ('most_recent_source' not in updated or
                    self.selected_data.shape[0] >= self.gals_max):
                return

            source = wwt.most_recent_source
            galaxy = source["layerData"]

            for k in ["ra", "decl", "z"]:
                galaxy[k] = float(galaxy[k])

            galaxy['element'] = galaxy['element'].replace("?", "α")  # Hacky fix for now
            fov = min(wwt.get_fov(), GALAXY_FOV)

            self.go_to_location(galaxy["ra"], galaxy["decl"], fov=fov)
            self.current_galaxy = galaxy
            self.candidate_galaxy = galaxy

            if not self.selected_data.empty:
                gal_names = [k for k in self.selected_data["name"]]

                if self.current_galaxy["name"] in gal_names:
                    self.candidate_galaxy = {}

            self.selected = True

        self.widget.set_selection_change_callback(wwt_cb)

        super().__init__(*args, **kwargs)

    def show_galaxies(self, show=True):
        if show and self.sdss_layer is None:
            layer = self.widget.layers.add_table_layer(self.table)
            layer.marker_type = "gaussian"
            layer.size_scale = 100
            layer.color = "#00FF00"
            self.sdss_layer = layer
        elif not show:
            self.widget.layers.remove_layer(self.sdss_layer)
            self.sdss_layer = None

    @property
    def on_galaxy_selected(self):
        return self._on_galaxy_selected

    @on_galaxy_selected.setter
    def on_galaxy_selected(self, cb):
        self._on_galaxy_selected = cb

    def select_galaxy(self, galaxy):
        galaxy_df = DataFrame({k: [v] for k, v in galaxy.items()})
        self.selected_data = concat([self.selected_data, galaxy_df], ignore_index=True)
        self.selected_count = self.selected_data.shape[0]
        self._create_selected_layer()
        if self._on_galaxy_selected is not None:
            self._on_galaxy_selected(galaxy)
        self.selected = False

    def _create_selected_layer(self):
        self.table = Table.from_pandas(self.selected_data)
        layer = self.widget.layers.add_table_layer(self.table)
        layer.marker_type = "gaussian"
        layer.size_scale = 100
        layer.color = "#FF0000" # This will mix with #00FF00 above to make yellow
        if self.selected_layer is not None:
            self.widget.layers.remove_layer(self.selected_layer)
        self.selected_layer = layer

    def vue_select_current_galaxy(self, _args=None):
        self.select_galaxy(self.current_galaxy)
        self.current_galaxy = {}
        self.candidate_galaxy = {}

    def vue_reset(self, _args=None):
        self.widget.center_on_coordinates(self.START_COORDINATES, fov=FULL_FOV,
                                          instant=True)
        self.current_galaxy = {}
        self.candidate_galaxy = {}
        self.selected = False

    def go_to_location(self, ra, dec, fov=GALAXY_FOV):
        coordinates = SkyCoord(ra * u.deg, dec * u.deg, frame='icrs')
        instant = self.motions_left <= 0
        if not instant:
            self.motions_left -= 1
        self.widget.center_on_coordinates(coordinates, fov=fov,
                                          instant=instant)

    @observe('flagged')
    def mark_galaxy_bad(self, change):
        if not change["new"]:
            return
        if self.current_galaxy["id"]:
            data = {"galaxy_id": int(self.current_galaxy["id"])}
        else:
            name = self.current_galaxy["name"]
            if not name.endswith(".fits"):
                name += ".fits"
            data = {"galaxy_name": name}
        self._request_session.put(f"{API_URL}/{HUBBLE_ROUTE_PATH}/mark-galaxy-bad",
                     json=data)
