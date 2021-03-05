# CoSplit artefact - PLDI21 paper 885

If you run into issues with the virtual machine, see the troubleshooting section
at the end of this file.

## Getting Started Guide (Kick the Tires)

The artefact consists of a virtual machine image.

Download VirtualBox from https://www.virtualbox.org/wiki/Downloads. We used
version 6.1.18. Older versions may work, but especially if you are running
Windows and use HyperV (e.g. WSL2 or Docker), we recommend the latest version.

The login details are user 'pldi21' with password 'pldi21' (without quotes).

**TODO: add instructions of how to import the VM**

Once you start the VM:

1. Open a terminal and change directory to `~/cosplit-artefact`

2. Inspect the `~/cosplit-artefact/fig/` folder to see the plots that were
   generated on the authors' machine. Run `make clean` to delete them.

3. Run `make`. This should take roughly 3.5 minutes and will produce figures in
   the `~/cosplit-artefact/fig/` folder:
   
   - `trans.pdf` corresponding to the inline figure in section 5.1.2 (line 1034)
   - `timing.pdf` corresponding to Figure 12 (line 1050)
   - `maxgesize.pdf` and `maxgenumber.pdf` corresponding to, respectively, the
     left and right parts of Figure 13 (line 1101)

4. Check that these figures match the ones in the paper. `timing.pdf` may
   look slightly different, as it measures performance.

5. Open a terminal navigate to `~/cosplit-artefact/eth-usage-analysis`. In the
   terminal, run `jupyter notebook`. This should open an instance of Jupyter
   Notebook in Firefox. Click on the `Ethereum smart contract usage.ipynb`
   entry. On the left-hand side of the page, the inputs are numbered:

   - `In[20]` corresponds to the left part of Figure 1 (line 170)
  
   - The right part of Figure 1 (line 170) is obtained from the data in `In[25]`
     (exported to `eth-erc20-split.csv`) by considering only `erc20_transfer`
     and `non_erc20_single_call` (and normalising such that their sum is 100%).

6. Check that these figures match the ones in the paper.

## List of claims

**Claims supported by the artefact:**

1. In Ethereum, user-to-user transfers are on a solid downward trend (line 213).
   
2. In Ethereum, single contract transactions take up to 55% of the latest blocks
   in our sample (which ends at block 9.25M / Jan 2020) (line 215).

3. In Ethereum ERC20 token transfers are a significant portion of single calls
   (lines 217-218).

4. The CoSplit analysis can be run offline to identify the maximal set of
   transitions that can be sharded for a contract (line 1090-1093).
  
  - The alternatives are shown in the `Maximal selections` column of
    `benchmarks/goodenough.csv`. Different sets of transitions (selections) are
    separated by the keyword `OR`.

5. The CoSplit analysis adds a significant, but acceptable overhead of around
   46% to the total contract deployment time (lines 1026-1028, Figure 12).

6. CoSplit uncovers many opportunities for parallel execution of smart
   contracts. That is, the largest shardable ("good enough") signature is, for
   many contracts in our dataset, large relative to the contract's total number
   of transitions (line 1094, Figure 13).

**Claims NOT supported by the artefact:**

1. When integrated with Zilliqa, CoSplit shows an increase in throughput linear
   in the number of shards for specific workloads (FungibleToken,
   NonfungibleToken, Unstoppable Domains registry) (lines 1172-1207).

   - We include the source code of these contracts, as well as transaction
     workloads (`traces`) that we used for benchmarking throughput.

2. Our integration of CoSplit with Zilliqa introduces an approximately 60x
   overhead to transaction dispatch time (8 microseconds to 475 microseconds)
   and state delta merging (0.8 microseconds to 48.65 microseconds per state
   entry).

## Step-by-Step Instructions (Full Review)


1. Run the steps in the 'Getting Started' section


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

- **The Virtual Box display window becomes black.** This sometimes happens on
  high-resolution monitors. When it happens, resize the Virtual Box window (by
  dragging from the corner) to make it smaller. The VM display should become
  functional again.

- **The VM freezes.** Make sure you are using the latest version of Virtual Box,
  especially if you are running Windows and have HyperV enabled (e.g., you use
  WSL2 or Docker). Earlier versions of Virtual Box only had experimental support
  for HyperV -- the VM would run, but would be unstable.

- **Copy/paste does not work between my machine and the VM.** In the Virtual Box
  window, select Devices -> Shared clipboard -> Bidirectional.

- **I cannot unzip `eth-usage-dataset.zip`.** Use `7za x eth-usage-dataset.zip`
  rather than the `unzip` command.
