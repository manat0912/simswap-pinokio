import os
import cv2
import torch
import shutil
import numpy as np
from PIL import Image
import torch.nn.functional as F
from torchvision import transforms
import gradio as gr
from models.models import create_model
from options.test_options import TestOptions
from insightface_func.face_detect_crop_multi import Face_detect_crop
from util.reverse2original import reverse2wholeimage
from util.add_watermark import watermark_image
from util.norm import SpecificNorm
from parsing_model.model import BiSeNet
from util.videoswap import video_swap

def _totensor(array):
    tensor = torch.from_numpy(array)
    img = tensor.transpose(0, 1).transpose(0, 2).contiguous()
    return img.float().div(255)

class SimSwapApp:
    def __init__(self):
        self.opt = None
        self.model = None
        self.spNorm = None
        self.app = None
        self.net = None
        self.transformer_Arcface = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def load_models(self, crop_size=224, use_mask=True):
        if self.model is not None and self.opt.crop_size == crop_size and (self.net is not None) == use_mask:
            return

        options = TestOptions()
        options.initialize()
        args = ["--Arc_path", 'arcface_model/arcface_checkpoint.tar', "--isTrain", "False", "--no_simswaplogo", "--crop_size", str(crop_size)]
        if not torch.cuda.is_available():
            args.extend(["--gpu_ids", "-1"])
        
        self.opt = options.parser.parse_args(args)
        self.opt.use_mask = use_mask
        
        torch.nn.Module.dump_patches = True
        self.model = create_model(self.opt)
        self.model.eval()
        self.spNorm = SpecificNorm()

        mode = 'ffhq' if crop_size == 512 else 'None'
        self.app = Face_detect_crop(name='antelope', root='./insightface_func/models')
        self.app.prepare(ctx_id=0 if torch.cuda.is_available() else -1, det_thresh=0.6, det_size=(640, 640), mode=mode)

        if use_mask:
            n_classes = 19
            self.net = BiSeNet(n_classes=n_classes)
            if torch.cuda.is_available():
                self.net.cuda()
            save_pth = os.path.join('./parsing_model/checkpoint', '79999_iter.pth')
            if os.path.exists(save_pth):
                self.net.load_state_dict(torch.load(save_pth, map_location=self.device))
                self.net.eval()
            else:
                print(f"Warning: Parsing model not found at {save_pth}. Masking will be disabled.")
                self.net = None
                self.opt.use_mask = False
        else:
            self.net = None

    def swap_image(self, source_img, target_img, crop_size, use_mask):
        self.load_models(crop_size, use_mask)
        
        with torch.no_grad():
            img_a_whole = cv2.imread(source_img)
            img_a_align_crop, _ = self.app.get(img_a_whole, crop_size)
            img_a_align_crop_pil = Image.fromarray(cv2.cvtColor(img_a_align_crop[0], cv2.COLOR_BGR2RGB))
            img_a = self.transformer_Arcface(img_a_align_crop_pil)
            img_id = img_a.view(-1, img_a.shape[0], img_a.shape[1], img_a.shape[2]).to(self.device)

            img_id_downsample = F.interpolate(img_id, size=(112, 112))
            latend_id = self.model.netArc(img_id_downsample)
            latend_id = F.normalize(latend_id, p=2, dim=1)

            img_b_whole = cv2.imread(target_img)
            img_b_align_crop_list, b_mat_list = self.app.get(img_b_whole, crop_size)
            
            swap_result_list = []
            b_align_crop_tenor_list = []

            for b_align_crop in img_b_align_crop_list:
                b_align_crop_tenor = _totensor(cv2.cvtColor(b_align_crop, cv2.COLOR_BGR2RGB))[None, ...].to(self.device)
                swap_result = self.model(None, b_align_crop_tenor, latend_id, None, True)[0]
                swap_result_list.append(swap_result)
                b_align_crop_tenor_list.append(b_align_crop_tenor)

            output_dir = 'output'
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            output_path = os.path.join(output_dir, 'result.jpg')
            
            logoclass = watermark_image('./simswaplogo/simswaplogo.png')
            reverse2wholeimage(b_align_crop_tenor_list, swap_result_list, b_mat_list, crop_size, img_b_whole, logoclass,
                               output_path, self.opt.no_simswaplogo, pasring_model=self.net, use_mask=self.opt.use_mask, norm=self.spNorm)
            
            return output_path

    def swap_video(self, source_img, target_video, crop_size, use_mask):
        self.load_models(crop_size, use_mask)
        
        with torch.no_grad():
            img_a_whole = cv2.imread(source_img)
            img_a_align_crop, _ = self.app.get(img_a_whole, crop_size)
            img_a_align_crop_pil = Image.fromarray(cv2.cvtColor(img_a_align_crop[0], cv2.COLOR_BGR2RGB))
            img_a = self.transformer_Arcface(img_a_align_crop_pil)
            img_id = img_a.view(-1, img_a.shape[0], img_a.shape[1], img_a.shape[2]).to(self.device)

            img_id_downsample = F.interpolate(img_id, size=(112, 112))
            latend_id = self.model.netArc(img_id_downsample)
            latend_id = F.normalize(latend_id, p=2, dim=1)

            output_dir = 'output'
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            output_path = os.path.join(output_dir, 'result.mp4')
            
            video_swap(target_video, latend_id, self.model, self.app, output_path, temp_results_dir='./temp_results', 
                       crop_size=crop_size, no_simswaplogo=self.opt.no_simswaplogo, use_mask=self.opt.use_mask)
            
            return output_path

simswap = SimSwapApp()

with gr.Blocks() as demo:
    gr.Markdown("# SimSwap Face Swapper")
    with gr.Tab("Image Swapping"):
        with gr.Row():
            with gr.Column():
                src_img = gr.Image(type="filepath", label="Source Image (Face to use)")
                tgt_img = gr.Image(type="filepath", label="Target Image (Image to swap into)")
                crop_size = gr.Radio([224, 512], label="Crop Size", value=224)
                use_mask = gr.Checkbox(label="Use Mask", value=True)
                btn_img = gr.Button("Swap Image")
            with gr.Column():
                out_img = gr.Image(label="Result")
        btn_img.click(simswap.swap_image, inputs=[src_img, tgt_img, crop_size, use_mask], outputs=out_img)

    with gr.Tab("Video Swapping"):
        with gr.Row():
            with gr.Column():
                src_img_vid = gr.Image(type="filepath", label="Source Image (Face to use)")
                tgt_vid = gr.Video(label="Target Video")
                crop_size_vid = gr.Radio([224, 512], label="Crop Size", value=224)
                use_mask_vid = gr.Checkbox(label="Use Mask", value=True)
                btn_vid = gr.Button("Swap Video")
            with gr.Column():
                out_vid = gr.Video(label="Result")
        btn_vid.click(simswap.swap_video, inputs=[src_img_vid, tgt_vid, crop_size_vid, use_mask_vid], outputs=out_vid)

if __name__ == "__main__":
    demo.launch()
