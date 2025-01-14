import numpy as np
import pandas as pd
import torch
from pathlib import Path
from PIL import Image
from random import randint
from torch.utils.data import Dataset
from tqdm.notebook import tqdm


uni2sym_df = pd.read_csv('./unicode_translation.csv')
forgotten = [{'Unicode': 'U+770C', 'char': '県'},
             {'Unicode': 'U+4FA1', 'char': '価'},
             {'Unicode': 'U+7A83', 'char': '窃'},
             {'Unicode': 'U+515A', 'char': '党'},
             {'Unicode': 'U+5E81', 'char': '庁'},
             {'Unicode': 'U+5039', 'char': '倹'}]
uni2sym_df = pd.concat([uni2sym_df, pd.DataFrame.from_records(forgotten)])
uni2class = dict(zip(uni2sym_df.Unicode, uni2sym_df.index.tolist()))
class2sym = dict(zip(uni2sym_df.index.tolist(), uni2sym_df.char))


def load_data(split):
    assert split in ('train', 'test')
    csv_split = 'train' if split == 'train' else 'sample_submission'
    df = pd.read_csv(f'./{csv_split}.csv', keep_default_na=False)
    image_path = Path(f'./data/{split}')

    images = []
    for id, row in tqdm(df.iterrows(), total=len(df)):
        id_name = row['image_id'] + '.jpg'
        image = {
            'file': Path.joinpath(image_path, id_name),
            'bboxes': [],
            'labels': []
        }
        if split == 'train':
            labels = row['labels'].split()
            assert len(labels) % 5 == 0
            n = len(labels) // 5
            for i in range(0, n):
                uni, x, y, w, h = labels[i * 5:(i + 1) * 5]
                image['bboxes'].append(np.array([int(x), int(y), int(w), int(h)]))
                image['labels'].append(uni2class[uni])
        else:
            image['useage'] = row['Useage']
        image['bboxes'] = np.array(image['bboxes'])
        image['labels'] = np.array(image['labels'])
        images.append(image)
    return images


def ourCrop(image, bboxes, labels, w, h, n_w, n_h, thresh=0.33):
    x0, y0 = randint(0, w - n_w), randint(0, h - n_h)
    x1, y1 = x0 + n_w, y0 + n_h
    new_bboxes = []
    new_labels = []
    # print('crop', x0, y0, x1, y1)
    for i, bbox in enumerate(bboxes):
        # print(bbox)
        intersec = (min(x1, bbox[0] + bbox[2]) - max(x0, bbox[0])) * (min(y1, bbox[1] + bbox[3]) - max(y0, bbox[1]))
        if intersec / bbox[2] / bbox[3] > thresh:
        # if bbox[0] >= x0 and bbox[1] >= y0 and bbox[0] + bbox[2] <= x1 and bbox[1] + bbox[3] <= y1:
            new_bboxes.append(np.array([bbox[0] - x0, bbox[1] - y0, bbox[2], bbox[3]]))
            new_labels.append(labels[i])
    if isinstance(image, torch.Tensor) or isinstance(image, np.ndarray):
        new_image = image[x0:x1, y0:y1]
    elif isinstance(image, Image.Image):
        new_image = image.crop((x0, y0, x1, y1))
    else:
        raise ValueError('unknown image type in crop')
    return new_image, np.array(new_bboxes), np.array(new_labels)


class DetectionDataset(Dataset):
    def __init__(self, images, max_size=None, crop_size=(1024, 1024), transforms=None, threshold=0.5):
        if isinstance(crop_size, int):
            crop_size = (crop_size, crop_size)
        if isinstance(images, str):
            self.images = load_data(images)
        else:
            self.images = images
        self.max_size = max_size
        self.crop_size = crop_size
        self.transforms = transforms
        self.threshold = threshold

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        image = Image.open(self.images[idx]['file'])
        bboxes = self.images[idx]['bboxes']  # pixels: (x, y, w, h)
        labels = self.images[idx]['labels']
        if self.max_size is not None:
            ratio = self.max_size / max(image.width, image.height)
            bboxes = (bboxes.astype(float) * ratio).astype(int)
            image = image.resize((int(image.width * ratio), int(image.height * ratio)))
        # note that the boxes after this line might go over the borders (if we have to crop them, we have to change the new_boxxes.append line in ourCrop)
        image, bboxes, labels = ourCrop(image, bboxes, labels, image.width, image.height, *self.crop_size, self.threshold)
        if self.transforms is not None:
            image = self.transforms(image)
        return image, bboxes, labels
