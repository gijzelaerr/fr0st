"""Run through the entire flame file as a single animation, in a
loop. Can be used to preview sheep or other kinds of
animation."""

flames = get_flames()
while True:
    for f in flames:
        preview(f)