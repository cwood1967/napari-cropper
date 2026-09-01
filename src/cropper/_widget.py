
from typing import List
import pathlib

import tifffile
#import dask
import dask.array as da
import napari
#import napari.types
#from magicgui.widgets import create_widget, Container
from magicgui import magicgui, magic_factory
from napari.utils._magicgui import find_viewer_ancestor


def _get_image_layers(gui):
    viewer = find_viewer_ancestor(gui.native)
    if viewer is None:
        return []
    return [layer for layer in viewer.layers if isinstance(layer, napari.layers.Image)]


def _init_widget(widget):
    widget.max_height = 250
    
@magic_factory(
    call_button = "Save Selected",
    directory = {"mode": "d", "label": "Choose a folder:"},
    target_layers = {"widget_type": "Select",
                     "choices": _get_image_layers,
                     "allow_multiple": True},
    widget_init=_init_widget,
    labels=False
)
def crop_widget(
    roi_layer: napari.layers.Shapes,
    target_layers: List[napari.layers.Image],
    directory: pathlib.Path
) -> None:
    
    box_coords_all = roi_layer.data[0]
    box_coords = box_coords_all[:, [-2, -1]]
    
    print(box_coords)
    ymin, xmin = box_coords.min(axis=0).astype(int)
    ymax, xmax = box_coords.max(axis=0).astype(int)
    
    res_list = []
    
    print(ymin, ymax, xmin, xmax)
    for img_layer in target_layers:
        if img_layer.multiscale:
            img = img_layer.data[0]
        else:
            img = img_layer.data
        
        if img.shape[-1] in [3, 4]:
            #if img.ndim > 3:
            cropped  = img[..., ymin:ymax, xmin:xmax, :]
            #else:
            #    cropped = img[ymin:ymax, xmin, xmax, :]
        else:
            if img.ndim > 2:
                cropped = img[..., ymin:ymax, xmin:xmax]
            else:
                cropped = img[ymin:ymax, xmin:xmax]
                
        print(cropped.shape)    
        res_list.append(cropped)
    
    print(len(res_list))
    if len(res_list) == 1:
        res = res_list[0]
    else:
        res = da.stack(res_list, axis=0)
    
    if res.shape[-1] in [3, 4]:
        axes = "TZYXC"
        photometric = "rgb"
        #res = da.moveaxis(res, -1, -3)
    else:
        axes = "TZCYX"
        photometric = "minisblack"
        
    axes = axes[-res.ndim:]
    
    
    print(res.shape, cropped.shape, axes)
    fname = f"{ymin:05d}_{xmin:05d}.tif"
    tifffile.imwrite(directory / fname, res,
                     imagej=False, ome=True,
                     photometric=photometric,
                     metadata={
                         "axes":axes,
                    #     "mode":"composite"
                     }) 
    return None
