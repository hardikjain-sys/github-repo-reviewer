import json

def makeBatch(files, max):
    batches = []
    cB = []
    size = 0

    for file in files:
        l = len(json.dumps(file))

        if cB and size + l > max:
            batches.append(cB)
            cB = []
            size = 0
        cB.append(file)
        size += l
    if cB:
        batches.append(cB)

    return batches