import json


def decode_frame(frame, tags=None):
    """ Extract tag values from frame
    :param frame: bytes or str object
    :param tags: specific tags to extract from frame
    :return: dictionary of values
    """

    # extract string and convert to JSON dict
    framebytes = frame if isinstance(frame, bytes) else frame.bytes
    if framebytes[-1] == 0:
        framestring = framebytes[:-1].decode('utf-8')
    else:
        framestring = framebytes.decode('utf-8')
    framedict = json.loads(framestring)

    # extract tags
    if tags:
        if isinstance(tags, str):
            tags = [tags]
        tagdict = {k:framedict[k] for k in tags if k in framedict}
    else:
        tagdict = framedict
    return tagdict


def decode_header(header):
    tags = ['htype', 'mapping', 'master_file', 'reporting']
    return decode_frame(header, tags)


def decode_frame_header(frame):
   tags = ['frame', 'series']
   return decode_frame(frame, tags)
