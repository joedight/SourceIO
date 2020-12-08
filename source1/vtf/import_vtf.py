import bpy
from pathlib import Path

import numpy as np

from ..vtf.VTFWrapper import VTFLib
from ..vtf.VTFWrapper.VTFLibEnums import ImageFlag

vtf_lib = VTFLib.VTFLib()


def import_texture(path):
    path = Path(path).absolute()
    name = path.stem
    print('Loading {}'.format(name))
    vtf_lib.image_load(str(path))
    if not vtf_lib.image_is_loaded():
        raise Exception(
            "Failed to load texture :{}".format(
                vtf_lib.get_last_error()))
    rgba_data = vtf_lib.convert_to_rgba8888()
    rgba_data = vtf_lib.flip_image_external(rgba_data, vtf_lib.width(), vtf_lib.height())
    pixels = np.array(rgba_data.contents, np.uint8)
    pixels = pixels.astype(np.float16, copy=False)
    try:
        image = bpy.data.images.get(name + '_RGB', None) or bpy.data.images.new(
            name,
            width=vtf_lib.width(),
            height=vtf_lib.height())
        pixels = np.divide(pixels, 255)
        image.pixels = pixels
        image.alpha_mode = 'CHANNEL_PACKED'
        image.pack()
    except Exception as ex:
        print('Caught exception "{}" '.format(ex))
    vtf_lib.image_destroy()

    return name
