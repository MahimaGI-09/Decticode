from pymongo import MongoClient
import sys

def main():
    try:
        c = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=3000)
        info = c.server_info()
        print('connected', info.get('version'))
    except Exception as e:
        print('error', repr(e))
        sys.exit(1)

if __name__ == '__main__':
    main()
