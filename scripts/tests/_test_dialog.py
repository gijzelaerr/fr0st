res = dialog("please choose some stuff.",
             ("string", str),
             ("integer", int),
             ("float", float),
             ("boolean", bool),
             ("Including a default", int, 42),
             ("choices", ["spam", "ham", "eggs"], 1),
             ("Select between xforms.\nCool, isn't it?", flame.xform)
             )


for i in res:
    print i
