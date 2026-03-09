from rembg import remove, new_session
import os

def remove_background_web(input_path, output_path):
    try:
        with open(input_path, 'rb') as i:
            input_data = i.read()

        # 🧠 THE UPGRADE: 'isnet-general-use' is highly accurate for complex edges
        my_session = new_session("isnet-general-use")

        # 🎛️ THE TWEAK: We lower the foreground threshold and erode size. 
        # This tells the math: "When in doubt, KEEP the dark pixels, do NOT delete them!"
        output_data = remove(
            input_data, 
            session=my_session,
            alpha_matting=True,
            alpha_matting_foreground_threshold=200, # Lowered from 240
            alpha_matting_background_threshold=15,
            alpha_matting_erode_size=5              # Lowered from 10 to stop "biting" into the hair
        )

        with open(output_path, 'wb') as o:
            o.write(output_data)
            
        return True
    except Exception as e:
        print(f"🚨 Background Removal Failed: {e}")
        return False