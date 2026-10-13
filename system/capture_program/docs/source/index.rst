.. Millimeter-wave Capture Standard (mmwave-capture-std) documentation master file, created by
   sphinx-quickstart on Fri Jun  2 20:04:11 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. rst-class:: hide-header

Welcome to Millimeter-wave Capture Standard (mmwave-capture-std)'s documentation!
=================================================================================

**mmwave-capture-std** is a *fast*, *reliable*, and *replicable* Texas Instruments millimeter-wave capture toolkit, focus on data capturing and raw data parsing.

The supported project deployment uses Raspberry Pi 4 as the only acquisition
host. IWR1843BOOST USB, DCA1000EVM Ethernet, and ADXL355 SPI/DRDY all connect to
the Pi. The operator computer only reaches the Pi through Wi-Fi/SSH, while
IWR1843BOOST and DCA1000EVM are joined by their 60-pin HD connector.

Synchronized radar and ADXL355 capture is available in two modes. The
``software_timestamp`` mode brackets ``sensorStart`` on the Pi monotonic clock
and needs no radar GPIO wire. The ``hardware_trigger`` mode drives Pi GPIO18 to
IWR1843BOOST J6-9 ``SYNC_IN`` and can observe the same edge on GPIO24. Both
modes retain the 1 kHz ADXL355 DRDY timestamps from GPIO25.

.. warning::

   Source code and focused mock tests are not a powered bench validation. Keep
   ``hardware_validated = false`` until the actual firmware, J6 routing,
   waveform, frame correspondence, and latency have been measured.

It stands out with three key attributes:

#. **Fast**: It parses raw data into ``np.ndarray[np.complex64]`` 2.09 times faster than state-of-the-art packages (0.593s v.s. 1.239s).

#. **Reliable**: It makes users easily identify and debug hardware issues, and provides fine-grained control over different hardware. It achieves this by comprehensive logging (stderr & file) and by separating the hardware setup from the data capture code.

#. **Replicable**: It simplifies the process of replicating the recording setup by using a toml config file to manage capture hardware, layout the dataset as HDF5-like structure, and provide sensor config files to each capture result.

Here is an example of running ``mmwave-capture-std`` locally on the Pi to
capture data from IWR1843BOOST and DCA1000EVM:

.. code-block:: bash

   $ uv run mmwavecapture-std examples/capture_iwr1843.toml
   2023-06-02 :43.91 | INFO     | ...:...:225 - Capture ID: 0
   2023-06-02 :43.91 | INFO     | ...:init_hw:230 - Initializing capture hardware `iwr1843`..
   2023-06-02 :49.32 | SUCCESS  | ...:init_hw:245 - Capture hardware `iwr1843` initialized
   2023-06-02 :49.32 | SUCCESS  | ...:init_hw:247 - Total of 1 capture hardware initialized
   2023-06-02 :49.32 | INFO     | ...:capture:258 - Adding capture hardware `iwr1843`
   2023-06-02 :49.32 | INFO     | ...:capture:121 - Preparing capture hardware
   2023-06-02 :49.32 | INFO     | ...:capture:125 - Starting capture hardware
   2023-06-02 :49.42 | SUCCESS  | ...:capture:128 - Capture started
   2023-06-02 :52.49 | INFO     | ...:capture:132 - Capture finished
   2023-06-02 :52.49 | INFO     | ...:capture:134 - Dumping capture hardware configurations
   2023-06-02 :52.49 | SUCCESS  | ...:capture:270 - Capture finished, all files ...


Nice and easy! Your capture result will be stored like this with HDF5-like structure :

.. code-block:: bash

   ☁  mmwave-capture-std [main]  tree example_dataset
   example_dataset
    └── capture_00000
        ├── capture.log
        ├── config.toml
        └── iwr1843
            ├── dca.json
            ├── dca.pcap
            └── radar.cfg

You probably will need to modify the configuration to reflect your capture hardware setup.
Change the following setting in ``example/capture_iwr1843.toml`` to your setup:
(assume you did not change any setting on DCA1000EVM EEPROM)

.. code-block:: toml

   [hardware.iwr1843]
   dca_eth_interface = "eth0"
   radar_config_port = "/dev/ttyACM0"
   radar_data_port = "/dev/ttyACM1"
   capture_frames = 10

For a combined radar and ADXL355 run, build the Linux GPIO uAPI v2 native
helpers and start with the software timestamp example:

.. code-block:: bash

   make -C native/adxl355_capture
   make -C native/adxl355_capture print-hw
   make -C native/frame_trigger
   uv run mmwavecapture-std examples/capture_synchronized_software.toml

The hardware-trigger example is
``examples/capture_synchronized_hardware.toml``. It additionally requires
GPIO18 (physical pin 12) to J6-9 ``SYNC_IN`` and a common ground. GPIO24 is an
optional diagnostic branch enabled only with ``use_loopback = true`` and
``loopback_line = 24``. See :doc:`Setup <setup>` before
powering the fixture. Trigger frequency is limited to 90% of nominal radar
frame rate, and both initial delay and trigger period must stay below the
conservative 5-second DCA guard. Normal/SIGTERM cleanup only makes a best-effort
attempt to leave GPIO18 low; real fixtures should use a hardware pull-down and
have the waveform measured.

A successful combined run publishes radar and ADXL355 algorithm-input
packages plus ``sync/timeline.json`` and
``sync/radar_frame_monotonic_ns.npy``. The software timeline is an estimate
from the ``sensorStart`` bracket and the decoded radar manifest's nominal frame
period. The hardware timeline uses a physical loopback edge or, without
loopback, a userspace GPIO-set-completion reference that is not claimed as an
observed edge. Neither is represented as radar ADC sampling time, and DCA PCAP
timestamps remain Ethernet receive times. Loading requires the complete
sibling sync manifest and any capture-root status in addition to the decoded
radar package; the returned object exposes that combined manifest.


Where to start?
---------------

First, setup your environment (hardware, software, and network): :doc:`Setup <setup>`.

Then, read our quickstart to get familiar with how ``mmwave-capture-std`` works: :doc:`Quickstart <quickstart>`.



Contribute
----------

Use the following snippet to setup your development environment:

.. code-block:: bash

   git clone <repo-url>
   cd mmwave-capture-std
   uv sync # Prepare env and install deps
   uv run pre-commit install # Install pre-commit hooks

License
-------

This project is licensed under the `BSD 3-Clause Clear License <https://github.com/mmwave-capture-std/mmwave-capture-std/blob/main/LICENSE>`_.


.. toctree::
   :caption: User's Guide
   :maxdepth: 2
   :hidden:

   setup
   quickstart
   configs/index

.. toctree::
   :caption: Development
   :hidden:

   api/api

.. toctree::
   :caption: Links
   :hidden:

   Homepage <https://cs.unc.edu/~louielu/p/mmwave-capture-std>
   Documentation <https://mmwave-capture-std.readthedocs.io/en/latest/>
   Source Code <https://github.com/mmwave-capture-std/mmwave-capture-std>
   License <https://github.com/mmwave-capture-std/mmwave-capture-std/blob/main/LICENSE>

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
