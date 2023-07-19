import sys
from os import listdir
from os.path import getsize, isfile, join


def main(argv):
    if "release/" in argv[0]:
        file_list = sorted(
            [f for f in listdir("./changelog") if isfile(join("./changelog", f))]
        )
        file_list.reverse()
        latest_file = file_list[0].replace(".md", "")
        release_date = argv[0].replace("release/", "")
        if latest_file != release_date:
            print("No matching changelog for release branch.")
            sys.exit(0)
        else:
            data = "# Changelog\n\n"

            for i, v in enumerate(file_list):
                data = data + "## " + v.replace(".md", "") + "\n\n"
                with open(f"./changelog/{v}", "r") as f:
                    data = data + f.read()
                    if i != (len(file_list) - 1):
                        data = data + "\n"

            try:
                original_size = getsize("./CHANGELOG.md")
            except OSError:
                original_size = 0

            with open("./CHANGELOG.md", "w") as f:
                f.write(data)
            new_size = getsize("./CHANGELOG.md")

            if new_size != original_size:
                print("CHANGELOG.md updated.")
                sys.exit(0)

            print("CHANGELOG.md, No changes.")
            sys.exit(0)

    print("Not a release branch")
    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv[1:])
