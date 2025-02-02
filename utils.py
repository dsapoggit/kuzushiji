import numpy as np
import torch
import torchvision.transforms as T
from dataset import DetectionDataset, class2sym
from PIL import Image, ImageDraw, ImageFont


def draw_bboxes(image, bboxes, labels, order='xywh', mode='pixels'):
    if isinstance(image, np.ndarray) or isinstance(image, torch.Tensor):
        image = Image.fromarray(image)
    print(len(bboxes), 'bboxes')
    draw = ImageDraw.Draw(image)
    rgb = (255, 0, 0)
    for i, [x0, y0, x1, y1] in enumerate(bboxes):
        if mode == 'pixels':
            a0, b0, a1, b1 = x0, y0, x0 + x1, y0 + y1
        else:
            raise ValueError('unknown mode in draw bboxes')
        draw.rectangle([a0, b0, a1, b1], outline=rgb)
        draw.rectangle((x0, y0 - 14, x0 + 18, y0 + 4), fill=(255, 255, 255))
        fnt = ImageFont.truetype("/content/Arial Unicode MS.TTF", 14)
        draw.text((x0 + 2, y0 - 12), class2sym[labels[i]], fill=(0, 0, 0), font=fnt)
    return image


if __name__ == '__main__':
    train_ds = DetectionDataset('train', max_size=2048, transforms=T.Compose([T.ColorJitter(0.3, 0.5, 0.5, 0.1)]))
    draw_bboxes(*train_ds[0]).show()
