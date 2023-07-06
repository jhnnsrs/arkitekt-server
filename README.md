# arkitekt-server
This should serve as an entrypoint to the arkitekt platform, and describe the main entrypoints to onboard *developers*
of the backend of the platform.



### Do not look here if

-   you only want to use the platform (e.g. for image analysis), or develop
    functionality in form of connected app, please refer to the general [documentation](https://jhnnsrs.github.io/doks/) (ongoing effort)

-   you want to contribute to the development of the default arkitekt frontend
    orkestrator, this happens [here](https://github.com/jhnnsrs/orkestrator)

-   you want to contribute to the arkitekt management and installation software,
    konstruktor, [here](https://github.com/jhnnsrs/konstruktor)


## This Repo

This repo acts as a mono repo of the server side of the platform:
and comes with a default developer oriented docker-compose configuration to run on a local machine.
Development of the services is prodived in their dedicated repositories but come provided
as github submodules in this repo:

 - [lok](https://github.com/jhnnsrs/lok-server) (The authentication & authorization service)
 - [rekuest](https://github.com/jhnnsrs/rekuest-server) (The functionality repository)
 - [mikro](https://github.com/jhnnsrs/mikro-server) (The microscopy data service )
 - [fluss](https://github.com/jhnnsrs/fluss-server) (The workflow design backend )
 - [port](https://github.com/jhnnsrs/port-server) (The plugin (conzainerized apps) manager )


## Roadmap

This repo will increasingly contain more information for the onboarding process
and should stand as a central hub for issues on the platform








