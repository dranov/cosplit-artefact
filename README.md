# CoSplit artefact - PLDI21 paper 885

If you have cloned the artefact repository using `git pull`:
- Install `git-lfs` and run `git lfs fetch` and then `git lfs pull` inside the
  cloned folder. **(AE reviewers, you do not need to do this.)**

If you run into issues with the virtual machine, see the troubleshooting section
at the end of this file.

## Getting Started Guide (Kick the Tires)

The artefact consists of a virtual machine image.

Download VirtualBox from https://www.virtualbox.org/wiki/Downloads. We used
version 6.1.18.

The *login details* are user 'pldi21' with password 'pldi21' (without quotes).

## Step-by-Step Instructions (Full Review)


## Appendix

### Reference commands

Output the result of the sharding analysis for a given contract:

```
./bin/scilla-checker -gaslimit 10000 -libdir ./src/stdlib/ -sa  ~/cosplit-artefact/contracts/FungibleToken~zil1ygxmqm8rvgvvmy9a6jn04mtq3qssy9qws92lqr.scilla
```

Output the good enough information for a given contract:

```
./bin/scilla-checker -gaslimit 10000 -libdir ./src/stdlib/ -sa -sa-ge  ~/cosplit-artefact/contracts/FungibleToken~zil1ygxmqm8rvgvvmy9a6jn04mtq3qssy9qws92lqr.scilla 2>/dev/null | head -n 1 | sed 's/\[GoodEnough\] //'
```

To get the timing split between parsing/typechecking/sharding analysis:

```
./bin/scilla-checker -gaslimit 10000 -libdir ./src/stdlib/ -sa -sa-timings  ~/cosplit-artefact/contracts/FungibleToken~zil1ygxmqm8rvgvvmy9a6jn04mtq3qssy9qws92lqr.scilla 2>/dev/null | head -n3 | sed 's/\[Parse\] //' | sed 's/\[Typecheck\] '// | sed 's/\[Sharding\] //' | tr '\n' ',' | sed 's/,$//'
```



### Troubleshooting

- **My keyboard layout is not reflected in the VM.** The art

- **The Virtual Box display window becomes black.** This sometimes happens on
  high-resolution monitors. When it happens, resize the Virtual Box window (by
  dragging from the corner) to make it smaller. The VM display should become
  functional again.

- **Copy/paste does not work between my machine and the VM.** In the Virtual Box
  window, select Devices -> Shared clipboard -> Bidirectional.

- **I cannot unzip `eth-usage-dataset.zip`.** Use `7za x eth-usage-dataset.zip`
  rather than the `unzip` command.
