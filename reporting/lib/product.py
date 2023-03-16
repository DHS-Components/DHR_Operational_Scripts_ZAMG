products = {
    "S1": {
        "filter": "startswith(Name,'S1') and not substringof('_SLC_',Name)",
        "names": [ "S1A_", "S1B_", "S1A_.._RAW_", "S1B_.._RAW_", "S1A_.._GRDM", "S1B_.._GRDM", "S1A_.._GRDH", "S1B_.._GRDH", "S1A_.._GRDF", "S1B_.._GRDF", "S1A_.._OCN_", "S1B_.._OCN_" ]
    },
    "S1-SLC": {
        "filter": "startswith(Name,'S1') and substringof('_SLC_',Name)",
        "names": [ "S1A_", "S1B_", "S1A_.._SLC_", "S1B_.._SLC_" ]
    },
    "S2A-L1C": {
        "filter": "startswith(Name,'S2A_MSIL1C')",
        "names": [ "S2A_", "S2A_MSIL1C_" ]
    },
    "S2B-L1C": {
        "filter": "startswith(Name,'S2B_MSIL1C')",
        "names": [ "S2B_", "S2B_MSIL1C_" ]
    },
    "S2A-L2A": {
        "filter": "startswith(Name,'S2A') and substringof('MSIL2A',Name)",
        "names": [ "S2A_", "S2A_MSIL2A_" ]
    },
    "S2B-L2A": {
        "filter": "startswith(Name,'S2B') and substringof('MSIL2A',Name)",
        "names": [ "S2B_", "S2B_MSIL2A_" ]
    },
    "S3": {
        "filter": "startswith(Name,'S3')",
        "names": [ "S3A_", "S3B_", "S3A_SR_", "S3B_SR_", "S3A_OL_", "S3B_OL_", "S3A_SL_", "S3B_SL_" ]
    },
    "S5": {
        "filter": "startswith(Name,'S5')",
        "names": [ "S5P_.." ]
    }
}