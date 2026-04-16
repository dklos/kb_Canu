# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os

from kb_canu.CanuUtil import CanuUtil
#END_HEADER


class kb_canu:
    '''
    Module Name:
    kb_canu

    Module Description:
    KBase wrapper for the Canu long-read genome assembler.
    Supports Oxford Nanopore, PacBio CLR, and PacBio HiFi/CCS reads.
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Do not call self.ctx.log() from this function         #
    # as some log messages will be lost due to the usage    #
    # of gevent.                                            #
    #########################################               noqa
    VERSION = "0.0.1"
    GIT_URL = ""
    GIT_COMMIT_HASH = ""

    #BEGIN_CLASS_HEADER

    # Configure logging once at class level.  basicConfig is a no-op if a
    # handler is already installed, so this is safe to call multiple times.
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        level=logging.INFO,
    )

    #END_CLASS_HEADER

    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.config = config

        # Inject runtime env vars so CanuUtil can reach the callback server
        # and authenticate with the workspace.  These are set by the KBase
        # job runner inside the Docker container.
        self.config["SDK_CALLBACK_URL"] = os.environ.get(
            "SDK_CALLBACK_URL", config.get("SDK_CALLBACK_URL", "")
        )
        self.config["KB_AUTH_TOKEN"] = os.environ.get(
            "KB_AUTH_TOKEN", config.get("KB_AUTH_TOKEN", "")
        )

        # scratch is where all temporary files go; must be on a volume
        # shared between the module container and the callback server.
        self.config["scratch"] = config.get(
            "scratch",
            os.environ.get("SCRATCH", "/kb/module/work/tmp"),
        )
        os.makedirs(self.config["scratch"], exist_ok=True)

        #END_CONSTRUCTOR

    def run_kb_canu(self, ctx, params):
        """
        Run the Canu assembler on long-read sequencing data.

        :param ctx:    KBase context object (carries token, provenance, etc.)
        :param params: instance of type "CanuAssemblyParams"
        :returns:      list containing one instance of "CanuAssemblyOutput"
        """
        #BEGIN run_kb_canu

        # Forward the per-request token from the context so that all
        # workspace / service calls within CanuUtil use the caller's identity.
        runtime_config = dict(self.config)
        if ctx.get("token"):
            runtime_config["KB_AUTH_TOKEN"] = ctx["token"]

        # Attach provenance from the context so AssemblyUtil can record it.
        params["provenance"] = ctx.get("provenance", [])

        logging.info(
            "kb_canu.run_kb_canu called — workspace=%s  read_type=%s  genome_size=%s",
            params.get("workspace_name"),
            params.get("read_type"),
            params.get("genome_size"),
        )

        canu_util = CanuUtil(runtime_config)
        output = canu_util.run_kb_canu(params)

        logging.info(
            "kb_canu.run_kb_canu complete — report=%s",
            output.get("report_name"),
        )

        #END run_kb_canu
        return [output]

    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {
            "state":           "OK",
            "message":         "",
            "version":         self.VERSION,
            "git_url":         self.GIT_URL,
            "git_commit_hash": self.GIT_COMMIT_HASH,
        }
        #END_STATUS
        return [returnVal]
