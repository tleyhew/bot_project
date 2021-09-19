def validateConfig(config):
    #Make sure server_roles key exists
    assert "server_roles" in config
    
    #Make sure all server roles have a pronoun and can_serve value
    for key in config["server_roles"]:
        
        value = config["server_roles"][key]

        #Check that there's a pronoun
        assert "pronoun" in value
        assert type(value["pronoun"]) is str

        #Check that there's a can_serve key
        assert "can_serve" in value
        assert type(value["can_serve"]) is bool

    #Make sure there's minor roles
    assert "minor_roles" in config
    assert type(config["minor_roles"]) is list

    #Make sure there's exclusive roles
    assert "exclusive_roles" in config
    assert type(config["exclusive_roles"]) is list
    #Make sure every role in the exclusive list is a real role
    assert set(config["exclusive_roles"]).issubset(set(config["server_roles"]))

    #Make sure we specify a menu_page_size
    assert "menu_page_size" in config
    assert type(config["menu_page_size"]) is int

    #Make sure we have a drinkfile specified
    assert "drinkfile" in config
    assert type(config["drinkfile"]) is str

    #Make sure we have a token file specified
    assert "tokenfile" in config
    assert type(config["tokenfile"]) is str