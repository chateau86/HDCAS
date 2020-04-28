# HDCAS
Hard Drive Condition Alert System

Presentation video is available here: https://www.youtube.com/watch?v=UAZBYhaxzM4

# Dependencies
(In no particular order)
- Server
    - Python3
    - Postgresql 11
    - Direnv
    - Flask
    - Flask-sqlalchemy
    - simplejson
    - scikit-learn
- Client
    - Python3
    - SmartMonTools
    - pySMART.smartx

# Server deployment instruction

1. Get a server with all server dependencies up and running.
2. Apply all database schema from `server/migrations` in order using `psql`
3. Using `psql`, verify that any database account destined for server use can read/write to all the tables.
4. Configure `server/.envrc_local` to specify database URL in `DB_URL`. See `.envrc` for an example.
5. (optional) Set up Backblaze dataset:
    1. Set up a user to hold the Backblaze data
    2. Download Backblaze data to `loader/csv_data`
    3. Configure user token in `data_loader.py`
    4. Run `data_loader.py`
6. Start the server with `python3 server.py`
7. Test server for proper operation
