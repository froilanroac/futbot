import json
from time import sleep

def get_all_data(key, filename='src/database/db.json') -> list:
    '''Get all data from json file by key'''
    try:
        with open(filename, 'r') as f:
            database = json.load(f)
        return database[key]
    except:
        return []
    
def save_data(key, data, filename='src/database/db.json') -> str:
    '''Save data to json file by key'''
    try:
        with open(filename,'r') as f:
            database = json.load(f)
        database[key].append(data)
        with open(filename,'w') as f:
            json.dump(database, f, indent=4)
        return 'Data saved successfully'
    except Exception as e:
        return f'Error saving data: {e}'
    
def get_one(key, id, filename='src/database/db.json') -> dict:
    '''Get one element from json file by key and id'''
    try:
        with open(filename, 'r') as f:
            database = json.load(f)
        element = next((item for item in database[key] if str(item["id"]) == str(id)), False)
        return element
    except Exception as e:
        print(f'Error getting one element: {e}')
        return False
    
def delete_one(key, id, filename='src/database/db.json') -> str:
    '''Delete one element from json file by key and id'''
    try:
        with open(filename,'r') as f:
            database = json.load(f)
        database[key] = [e for e in database[key] if str(e['id']) != str(id)]
        with open(filename,'w') as f:
            json.dump(database, f, indent=4)
        return 'Data deleted successfully'
    except Exception as e:
        return f'Error deleting data: {e}'
    
def edit_list(value ,filename='src/database/db.json') -> str:
    '''Open json file'''
    try:
        with open(filename,'r') as f:
            database = json.load(f)
        database['lista_abierta'] = value
        with open(filename,'w') as f:
            json.dump(database, f, indent=4)
        return 'List state edited successfully'
    except Exception as e:
        return f'Error editing list state: {e}'
    
def get_list_state(filename='src/database/db.json') -> bool:
    '''Get list state'''
    try:
        with open(filename,'r') as f:
            database = json.load(f)
        return database['lista_abierta']
    except Exception as e:
        print(f'Error getting list state: {e}')
        return False
    
def autenticate_user(id, filename='src/database/db.json') -> bool:
    '''Autenticate user'''
    try:
        with open(filename,'r') as f:
            database = json.load(f)
        member = next((item for item in database['members'] if str(item["id"]) == str(id)), False)
        if member:
            return True
        else:
            return False
    except Exception as e:
        print(f'Error autenticating user: {e}')
        return False
    
def clear_list(key, filename='src/database/db.json') -> str:
    '''Clear list'''
    try:
        with open(filename,'r') as f:
            database = json.load(f)
        database[key] = []
        with open(filename,'w') as f:
            json.dump(database, f, indent=4)
        return 'List cleared successfully'
    except Exception as e:
        return f'Error clearing list: {e}'
    
def count_user_invitations(id, filename='src/database/db.json') -> int:
    '''Count user invitations'''
    try:
        with open(filename,'r') as f:
            database = json.load(f)
        invitations = [e for e in database['invitations'] if str(e['id']) == str(id)]
        return len(invitations)
    except Exception as e:
        print(f'Error counting user invitations: {e}')
        return 0
    
def delete_one_by_name(key, id, filename='src/database/db.json') -> str:
    '''Delete one element from json file by key and id'''
    try:
        with open(filename,'r') as f:
            database = json.load(f)
        database[key] = [e for e in database[key] if str(e['name']) != str(id)]
        with open(filename,'w') as f:
            json.dump(database, f, indent=4)
        return 'Data deleted successfully'
    except Exception as e:
        return f'Error deleting data: {e}'