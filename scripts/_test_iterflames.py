for i in self.tree.GetFlames():
    print i.name
print "---------------------------"

for i in self.tree.GetAllFlames():
    for j in i:
        print j
    print

