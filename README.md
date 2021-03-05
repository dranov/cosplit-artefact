# CoSplit artefact - PLDI21 paper 885

This document last updated on 2021-03-05 at 11:00 GMT.

If you run into issues with the virtual machine, see the troubleshooting section
at the end of this file.

**Reviewers:** run `git pull` and `git submodule update` in the
`cosplit-artefact` folder to receive the latest updates & instructions.

## Getting Started Guide (Kick the Tires)

Download VirtualBox from https://www.virtualbox.org/wiki/Downloads. We used
version 6.1.18. Older versions may work, but especially if you are running
Windows and use HyperV (e.g. WSL2 or Docker), we recommend the latest version.

Import the virtual machine image into Virtual Box.

The login details are user 'pldi21' with password 'pldi21' (without quotes).

Once you start the VM:

1. Open the `~/cosplit-artefact/fig/` folder to see the plots that were
   generated on the authors' machine. Run `make clean` to delete them.

2. Open a terminal and change directory to `~/cosplit-artefact`

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
     workloads (`traces`) that we used for benchmarking throughput. We also give
     instructions to spin up a Zilliqa locally network and provide the scripts
     to replay our transaction traces on a deployed Zilliqa network. However,
     running these in the virtual machine is impractical and would not provide
     any meaningful results. Unfortunately, we are unable to provide access to a
     cloud environment.
   - **Note**: if you try this process (explained in the Zilliqa subsection) in
     the VM, it will most likely not work. CPU usage gets pegged at 100% and the
     network has trouble even starting due to the high number of genesis
     accounts.

2. Our integration of CoSplit with Zilliqa introduces an approximately 60x
   overhead to transaction dispatch time (8 microseconds to 475 microseconds)
   and state delta merging (0.8 microseconds to 48.65 microseconds per state
   entry).

## Step-by-Step Instructions (Full Review)

Same as 'Kick the Tires' instructions.

Additionally, if you want to rebuild Scilla and Zilliqa:

1. Run `make clean` and `make` in the Scilla folder
2. Run `rm -rf build/` and `./build.sh` in the Zilliqa folder

If you want to explore the source code, we provide some pointers below.

### Folder structure

The `cosplit-artefact` folder consists of the following:

- `README.md` - the document you are reading now
- `pldi21-paper885.pdf` - the submission-version of the paper
- `eth-usage-analysis/` - contains `eth-usage-dataset.zip`, an archive of the
  data we used to compute the Ethereum statistics used in the motivation section
  of the paper, as well as the Jupyter Notebook used to plot the graphs
- `contracts/` - dataset of contracts used for the analysis benchmarks (Figure
  12 and Figure 13); the VM comes with an instance of Visual Studio Code
  installed, which you can use to inspect the contracts
- `scilla/` - the Scilla source code, with the CoSplit analysis included; the
  important files are:

  * `src/base/ShardingAnalysis.ml` is the main file, that performs the analysis
  * `src/server/sharding.ml` is invoked by the Zilliqa nodes to dispatch
    CoSplit-enabled transactions to the appropriate shard (function `get_shard`)
    AND to perform state delta merging (function `join`)
  * `src/base/Checker.ml` defines the various command line options

- `Zilliqa/` - the Zilliqa node source code, set up to use the CoSplit analysis

  * `src/libData/AccountData/Transaction.cpp`, method
    `Transaction::GetShardIndex` invokes the Scilla Server to determine which
    shard a CoSplit-enabled transaction should be sent to
  * `src/libPersistence/ContractStorage2.cpp`, method
    `UpdateStateDatasAndToDeletes` invokes the Scilla Server to determine how to
    merge shard state deltas coming from CoSplit-enabled smart contracts

 - `benchmarks` - scripts to compute the data for Figures 12 and 13 and to plot
   the figures
 - `throughput`
  
  * `contracts/` used for the throughput evaluation;
  * workload transaction traces (parameters used for CoSplit-enabled contract
    deployment are in `traces/with-cosplit/ss-deploy.trace`); except for
    contract deployment transactions, CoSplit-enabled and regular Zilliqa
    transactions are the same, so the files in `traces/` can be used for both
    CoSplit-enabled and non-CoSplit Zilliqa
  * `watch.py`, a script to inspect the state of a Zilliqa network
  * `replay-trace.py` executes a transaction trace whose path is passed as the
    first argument
  * `accounts.csv` and `accounts.xml` contain the account (pubkey, privkey)
    pairs and wallet addresses, respectively, of the accounts used in the
    transaction traces
  * The contents of `accounts.xml` need to be added to the `<accounts>` field in
    Zilliqa's `constants_local.xml` for the traces to be replayable
  * `fund.py` - a script to generate accounts and transaction traces; not
    directly used for benchmarking

  * `pyzil/` - a custom version of the PyZil Python library, used by the scripts
    in `throughput/`

### Reference commands

#### Scilla

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
#### Zilliqa

Spin up a local Zilliqa network (from `Zilliqa/build` folder):

```
./tests/Node/pre_run.sh && ./tests/Node/test_node_lookup.sh && ./tests/Node/test_node_simple.sh
```

If you want to have a different number of nodes/shards than the default, you
will have to edit `<COMM_SIZE>` in `constants_local.xml` and `num_ds` (number of
nodes per shard) and `num_shards` in `pre_run.sh` and `test_node_simple.sh`.

In the `throughput` folder, you can run `watch ./watch.py` to see the state of
the network.

Example of replaying traces:

`./replay-trace.py traces/with-cosplit/ss-deploy.trace`

## Appendix
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
  rather than the `unzip` command. The archive is heavily compressed (full size
  is ~15GB) and may take 3+ hours to unzip.
