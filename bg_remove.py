from rembg import remove, new_session
from PIL import Image
import os

def remove_background_web(input_path, output_path):
    try:
        # 1. Open the image and force it into RGBA (Red, Green, Blue, Alpha) mode
        img = Image.open(input_path).convert("RGBA")
        
        # 🌟 THE COLOR FIX: Save the original vibrant color profile!
        icc_profile = img.info.get('icc_profile')
        
        # --- THE BULLETPROOF RAM FIX ---
        img.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
        
        my_session = new_session("isnet-general-use")

        # 2. Ask the AI to ONLY generate the cut-out mask (Black & White silhouette)
        print("🧠 AI generating precision mask...")
        mask = remove(
            img, 
            session=my_session,
            only_mask=True, # 🌟 THE SECRET SAUCE: Do not let AI touch the colors!
            alpha_matting=True,
            alpha_matting_foreground_threshold=200, 
            alpha_matting_background_threshold=15,
            alpha_matting_erode_size=5              
        )

        # 3. Stamp the AI's mask onto our untouched, beautifully colored original image!
        img.putalpha(mask)

        # 4. Save the final PNG, injecting the original color profile back inside
        print("💾 Saving with 100% original color accuracy...")
        img.save(output_path, format="PNG", icc_profile=icc_profile)
            
        return True
    except Exception as e:
        print(f"🚨 Background Removal Failed: {e}")
        return False

# ==========================================
# 🌟 PRO TIER: BACKGROUND REPLACER
# ==========================================
def apply_pro_background(transparent_img_path, output_path, bg_color_hex=None, bg_image_path=None):
    """ Takes a transparent PNG and adds a solid color or custom image behind it. """
    try:
        fg = Image.open(transparent_img_path).convert("RGBA")
        
        if bg_image_path:
            bg = Image.open(bg_image_path).convert("RGBA")
            bg = bg.resize(fg.size, Image.Resampling.LANCZOS)
            bg.paste(fg, (0, 0), fg)
            bg.convert("RGB").save(output_path, format="JPEG")
            return True
            
        elif bg_color_hex:
            bg = Image.new("RGBA", fg.size, bg_color_hex)
            bg.paste(fg, (0, 0), fg)
            bg.convert("RGB").save(output_path, format="JPEG")
            return True
            
        return False
    except Exception as e:
        print(f"🚨 Pro Background Error: {e}")
        return False