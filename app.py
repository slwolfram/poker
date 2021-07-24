from poker import create_app

if __name__ == '__main__':
    create_app({'DBCONN': 'sqlite:///dev.db',
                'ENV': 'DEV'}).run()
