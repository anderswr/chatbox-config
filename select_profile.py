import sys
import shutil

if len(sys.argv) != 2:
    print("Bruk: python select_profile.py [profilnavn]")
    exit(1)

profile_name = sys.argv[1]
src = f"profiles/{profile_name}.json"
dst = "config.json"

shutil.copyfile(src, dst)
print(f"Aktivert profil: {profile_name}")
