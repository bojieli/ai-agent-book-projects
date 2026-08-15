import os


def main():
    from dotenv import load_dotenv
    load_dotenv()
    print(os.environ)
    uid = os.getenv('AWORLD_SEARCH_UID')
    print(uid)

if __name__ == "__main__":
    main()