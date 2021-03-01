registered_convs = []

def its_start_conv(user, command):
    for conv in registered_convs:
        if conv.this_is(user, command):
            return conv
