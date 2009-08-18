res = dialog("choose stuff", "please choose some stuff.",
             ("a long string", str),
             ("int", int),
             ("float", float),
             ("bool", bool),
             ("str_d", "hola"),
             ("int_d", 42),
             ("float_d", 7.1),
             ("bool_d", True))


for i in res:
    print i
