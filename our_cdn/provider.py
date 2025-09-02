import requests
import os

ORIGIN_LIST = ["http://127.0.0.1:5000","http://127.0.0.1:5001","http://127.0.0.1:5002"]

def upload_file(file_path):
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f)}
        for origin in ORIGIN_LIST:
            r = requests.post(f"{origin}/upload", files=files)
            if r.status_code == 200:
                print(f"Upload successful to {origin}")
                break
            else:
                print(f"Failed to upload to {origin}: {r.text}")

def delete_file(filename):
    for origin in ORIGIN_LIST:
        r = requests.delete(f"{origin}/delete/{filename}")
        print(f"Delete on {origin}: {r.text}")
        if r.status_code == 200:
            print(f"Delete successful on {origin}")
            break
        else:
            print(f"Failed to delete on {origin}: {r.text}")

if __name__ == '__main__':
    print("Content Provider Interface")
    print("1. Upload File")
    print("2. Delete File")
    choice = input("Enter choice (1 or 2): ")
    if choice == '1':
        path = input("Enter path to file: ")
        upload_file(path)
    elif choice == '2':
        fname = input("Enter filename to delete: ")
        delete_file(fname)
    else:
        print("Invalid choice")