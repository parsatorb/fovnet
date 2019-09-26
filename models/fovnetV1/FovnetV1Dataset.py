#Run as Python 3.7!
import random, sys
sys.path.insert(0, '../../fovnet/')
from remap import RGCMap, PyTorchImageSampler

sys.path.insert(0, '../')
from ModelUtils import get_top_corner
from ModelUtils import get_image_range
from ModelUtils import get_padding

from BaseDataset import BaseDataset

import numpy as np
from PIL import Image

from torchvision import transforms

class FovnetV1Dataset(BaseDataset):
    """Fovnet V1 Dataset: Polar retinal downsampling on one focal point"""

    def __init__(self, root_dir, centers_dir, transform=None, **kwargs):
        """
        Args:
            root_dir (string): Directory with all the images.
            centers_dir (string): location of focal points as pickle file
            transform (callable, optional): Optional transform to be applied
                on a sample.
        """
        
        super(FovnetV1Dataset, self).__init__(
            root_dir=root_dir, 
            centers_dir=centers_dir, 
            transform=transform, 
            **kwargs
        )
        
        self.crop_size=256
        
        rgcm = RGCMap((256,256), 70, .3, angle_steps=512, right=True)
        self.pytorch_sampler = PyTorchImageSampler(
            (256,256),
            rgcm.angles,
            rgcm.radial_pixel_positions,
            rgcm.centre_radii,
        )
        del rgcm
        
    def custom_transforms(self, image, center):
        #Random Horizontal flip
        if random.random() < 0.5:
            hFlip = True
            width = image.size[0]
            center = (width - center[0] - 1, center[1])
            image = transforms.functional.hflip(image)    
            
        image_range = get_image_range(center)
            
        padding = get_padding(image, image_range)
                
        upper_left = get_top_corner(center, padding, self.crop_size)
            
        ### Transforms
        #Pad
        image = transforms.Pad(padding, padding_mode="edge")(image)
        #Crop for foveation
        image = transforms.functional.crop(image,upper_left[0], upper_left[1], self.crop_size, self.crop_size)
        #Foveate
        image = np.array(image)
        if len(image.shape)==2:
            image = np.stack([image,image,image],axis=2)
                    
        warped_pytorch = self.pytorch_sampler(image)
        image = Image.fromarray(np.uint8(warped_pytorch*255))
        #Downsample
        image = transforms.Resize((45,23), Image.BOX)(image)
        
        if self.transform:
            image = self.transform(image)
            
        return image