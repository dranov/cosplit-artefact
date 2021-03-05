# Zilliqa Testbed

This repository contains scripts to test the performance of a locally
deployed Zilliqa network.

## Set-up

The default Zilliqa configuration file `constants_local.xml` is not
appropriate for testing. We need to make a few changes to the file:

### Enable smart contracts

Replace `/home/dranov/Developer` with your path to `scilla`.

```
<ENABLE_SC>true</ENABLE_SC>
<SCILLA_ROOT>/home/dranov/Developer/scilla</SCILLA_ROOT>
```

### Give genesis tokens to an account you control

Build Zilliqa and run `./bin/genkeypair` from the `build/` folder to
get a keypair,
e.g. `021E269B1A1509B417CD97795176235D948AF40CBCF9AC1393AA02CAA5E86C5177
6409DF90B2377C0103F1BD8CA7AB6BA4CB5FD07B937C10C27B9A1E4BBAE21897`
(pubkey, privkey). The address corresponding to that pubkey is:

```
./bin/getaddr --pubk 021E269B1A1509B417CD97795176235D948AF40CBCF9AC1393AA02CAA5E86C5177
1c2c7516dac2140c47cbae264e8349bb7c07a534
```

Then edit the configuration file:

```
<!-- These are the genesis accounts -->
<accounts>
    <account>
        <wallet_address>1c2c7516dac2140c47cbae264e8349bb7c07a534</wallet_address>
    </account>
</accounts>
```

### Permit sharding

```
<!-- Shard size will be automatically calculated if COMM_SIZE = 0 -->
<COMM_SIZE>0</COMM_SIZE>
```

## Build

Run `build.sh` to copy the edited configuration to the `build/`
directory (and compile the source code, if not already compiled).
