import shutil
import tkFileDialog
import os

OUTPUT_DIRECTORY = "/home/dale/Temp"
FILENAME = "image_test.pdf"

def file_save(source_file):
    f = tkFileDialog.asksaveasfile(mode='w', defaultextension=".pdf")
    if f is None: # asksaveasfile return `None` if dialog closed with "cancel".
        return
    target_path = f.name
    f.close()
    os.remove(target_path)
    shutil.move(source_file, target_path)



def main():
    file_save(os.path.join(OUTPUT_DIRECTORY, FILENAME))

if __name__ == '__main__':
    main()
