from glue.core import BaseData
from glue_jupyter.bqplot.image import BqplotImageView
from glue_jupyter.bqplot.profile import BqplotProfileView
from glue_jupyter.table import TableViewer
from jdaviz.core.events import (AddDataToViewerMessage,
                                RemoveDataFromViewerMessage)
from jdaviz.core.registries import viewer_registry
from specutils import Spectrum1D
from spectral_cube import SpectralCube
from echo import delay_callback
from astropy import units as u


__all__ = ['MOSVizProfileView', 'MOSVizImageView']


@viewer_registry("mosviz-profile-viewer", label="Profile 1D (MOSViz)")
class MOSVizProfileView(BqplotProfileView):
    default_class = Spectrum1D

    def data(self, cls=None):
        return [layer_state.layer.get_object(cls=cls or self.default_class)
                for layer_state in self.state.layers
                if hasattr(layer_state, 'layer') and
                isinstance(layer_state.layer, BaseData)]

    def set_plot_axes(self):
        data = self.data()[0]
        # Set axes labels for the spectrum viewer

        spectral_axis_unit_type = data.spectral_axis.unit.physical_type.title()
        # flux_unit_type = data.flux.unit.physical_type.title()
        flux_unit_type = "Flux density"

        if data.spectral_axis.unit.is_equivalent(u.m):
            spectral_axis_unit_type = "Wavelength"
        elif data.spectral_axis.unit.is_equivalent(u.pixel):
            spectral_axis_unit_type = "pixel"

        self.figure.axes[0].label = f"{spectral_axis_unit_type} [{data.spectral_axis.unit.to_string()}]"
        self.figure.axes[1].label = f"{flux_unit_type} [{data.flux.unit.to_string()}]"

        # Make it so y axis label is not covering tick numbers.
        self.figure.axes[1].label_offset = "-50"


@viewer_registry("mosviz-image-viewer", label="Image 2D (MOSViz)")
class MOSVizImageView(BqplotImageView):
    default_class = None

    def data(self, cls=None):
        return [layer_state.layer #.get_object(cls=cls or self.default_class)
                for layer_state in self.state.layers
                if hasattr(layer_state, 'layer') and
                isinstance(layer_state.layer, BaseData)]

    def set_plot_axes(self):
        self.figure.axes[1].tick_format = None
        self.figure.axes[0].tick_format = None

        self.figure.axes[1].label = "y: pixels"
        self.figure.axes[0].label = "x: pixels"

        # Make it so y axis label is not covering tick numbers.
        self.figure.axes[1].label_offset = "-50"


@viewer_registry("mosviz-profile-2d-viewer", label="Spectrum 2D (MOSViz)")
class MOSVizProfile2DView(BqplotImageView):
    # Due to limitations in CCDData and 2D data that has spectral and spatial
    #  axes, the default conversion class must handle cubes
    default_class = SpectralCube

    tools = ['bqplot:panzoom_x']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Setup viewer option defaults
        self.state.aspect = 'auto'
        self.state.add_callback('reference_data', self._update_world_axes, priority=100)

    def data(self, cls=None):
        return [layer_state.layer.get_object(cls=cls or self.default_class)
                for layer_state in self.state.layers
                if hasattr(layer_state, 'layer') and
                isinstance(layer_state.layer, BaseData)]

    def _update_world_axes(self, data):
        if data is not None:
            with delay_callback(self.state, 'x_att_world', 'y_att_world'):
                if 'Wave' in data.components:
                    self.state.x_att_world = data.id['Right Ascension']
                    self.state.y_att_world = data.id['Wave']

    def set_plot_axes(self):
        self.figure.axes[0].visible = False

        self.figure.axes[1].label = "y: pixels"
        self.figure.axes[1].tick_format = None
        self.figure.axes[1].label_location = "start"

        # Make it so y axis label is not covering tick numbers.
        self.figure.axes[1].label_offset = "-50"


@viewer_registry("mosviz-table-viewer", label="Table (MOSViz)")
class MOSVizTableViewer(TableViewer):
    def __init__(self, session, *args, **kwargs):
        super().__init__(session, *args, **kwargs)

        self.figure_widget.observe(self._on_row_selected, names=['highlighted'])

        self._selected_data = {}

    def _on_row_selected(self, event):

        # Grab the index of the latest selected row
        selected_index = event['new']
        mos_data = self.session.data_collection['MOS Table']

        for component in mos_data.components:
            comp_data = mos_data.get_component(component).data
            selected_data = comp_data[selected_index]

            if component.label == '1D Spectra':
                prev_data = self._selected_data.get('spectrum-viewer')
                if prev_data != selected_data:
                    remove_data_from_viewer_message = RemoveDataFromViewerMessage(
                        'spectrum-viewer', prev_data, sender=self)
                    self.session.hub.broadcast(remove_data_from_viewer_message)

                    add_data_to_viewer_message = AddDataToViewerMessage(
                        'spectrum-viewer', selected_data, sender=self)
                    self.session.hub.broadcast(add_data_to_viewer_message)

                    self._selected_data['spectrum-viewer'] = selected_data

            if component.label == '2D Spectra':
                prev_data = self._selected_data.get('spectrum-2d-viewer')
                if prev_data != selected_data:
                    remove_data_from_viewer_message = RemoveDataFromViewerMessage(
                        'spectrum-2d-viewer', prev_data, sender=self)
                    self.session.hub.broadcast(remove_data_from_viewer_message)

                    add_data_to_viewer_message = AddDataToViewerMessage(
                        'spectrum-2d-viewer', selected_data, sender=self)
                    self.session.hub.broadcast(add_data_to_viewer_message)

                    self._selected_data['spectrum-2d-viewer'] = selected_data

            if component.label == 'Images':
                prev_data = self._selected_data.get('image-viewer')
                if prev_data != selected_data:
                    remove_data_from_viewer_message = RemoveDataFromViewerMessage(
                        'image-viewer', prev_data, sender=self)
                    self.session.hub.broadcast(remove_data_from_viewer_message)

                    add_data_to_viewer_message = AddDataToViewerMessage(
                        'image-viewer', selected_data, sender=self)
                    self.session.hub.broadcast(add_data_to_viewer_message)

                    self._selected_data['image-viewer'] = selected_data

    def set_plot_axes(self, *args, **kwargs):
        return
