#!/bin/bash

# Script for detection and submission of gerrit changes

# detect_submit.sh - a. detect projects from the list of projects that have no change id
#                    b. create a change with "Depends-On" for them       
#                    c. output a list of change IDs for new changes

resubmit.sh - send revierify comment for a list	of changeIDs


DEFAULT_BRANCH=rhos-17.0-trunk-patches

# znoyder browse-osp packages --output osp-project

# Ask user which branch to use
read -p "Which branch to use? [$DEFAULT_BRANCH]: " input_branch
branch=${input_branch:-$DEFAULT_BRANCH}

# Ask user which gerrit to use
read -p "Which gerrit to use? [$DEFAULT_GERRIT]: " input_gerrit
gerrit=${input_gerrit:-$DEFAULT_GERRIT}

# TODO
# openstack-oslo.upgradecheck openstack-oslo.db openstack-oslo.policy openstack-oslo.privsep openstack-oslo.config
# openstack-designate-dashboard openstack-oslo.context openstack-kuryr openstack-oslo.cache openstack-heat-dashboard
# openstack-oslo.versionedobjects openstack-octavia-dashboard

declare -a COMPONENTS=(
python-sushy-oem-idrac
ansible-tripleo-ipa
networking-l2gw
python-manilaclient
python-os-vif
openstack-tripleo-puppet-elements
python-octaviaclient
openstack-tripleo-heat-templates
python-keystonemiddleware
python-networking-baremetal
oslo.utils
python-scciclient
aodh
python-saharaclient
python-heatclient
ovn-octavia-provider
openstack-ironic-inspector
openstack-tripleo-image-elements
python-mistralclient
python-designateclient
python-zaqarclient
python-ironic-lib
glance
python-os-brick
nova
python-mistral-lib
octavia
heat
python-networking-sfc
python-ovsdbapp
openstack-ironic-python-agent-builder
os-net-config
python-automaton
swift
python-dracclient
python-novaclient
python-barbicanclient
cinder
manila
manila-ui
python-neutronclient
keystone
ironic
python-os-ken
openstack-ironic-python-agent
oslo.middleware
python-neutron-lib
tripleo-ansible
python-stevedore
oslo.vmware
python-ironic-inspector-client
python-os-win
networking-bgpvpn
openstack-designate
ironic-prometheus-exporter
python-magnumclient
oslo.service
ironic-staging-drivers
python-openstackclient
ironic-ui
python-cinderclient
openstack-tripleo-validations
python-metalsmith
openstack-mistral
openstack-placement
python-glanceclient
python-castellan
oslo.serialization
openstack-heat-agents
python-openstacksdk
python-keystoneauth1
python-cliff
openstack-tripleo-common
oslo.messaging
horizon
python-osc-lib
openstack-neutron-dynamic-routing
python-sushy
python-octavia-lib
python-osc-placement
python-ironicclient
openstack-ec2-api
python-ceilometermiddleware
python-tripleoclient
python-cinderlib
python-tooz
glance_store
openstack-barbican
python-aodhclient
openstack-zaqar
python-keystoneclient
python-swiftclient
neutron
python-troveclient)

# TODO fix having same change ID (I6dcdd9099af2ece769c5eba32b4d69f29b28fd53) for cinder and ceilometer


declare -a CHANGE_IDs=(
Iaae62038d5e3f882ce840332cca4edc9cec46dc5 I82a3a021b7916de67d0fba295980e354d91afff9 I13ae8779567c24639426500f44a91feb8005a17c I09afffd7d225b7a098f9be36bc8d387a922583c3 I848b3a4831b8e6f8e695a337d22314268c2d6ff9 If3222f90c7e9e760ee15cb86feb07a008a87025f I282155aa70ae2a40d008c2a9cae38e97ae80bce6 I670cfcf7beae67fd8ae95c76a96433e681bf1aa5 Icffb5c8eff92c5a25ddd054d340326c43ca0b0da I99ed89b09f7ff8cec025f7e9d79f4b9115f2108e Ie8be1b40c8022791f8b751d138cfe1195e5e9e79 Ibc1997225455affeae0d4aa8b2cff0c040a6ffda I35f22915708a3cfbd01eb6e8450e552eaa2e61e4 Ia02e42202eaa08e46265513624b069a3144edf8a Ibbdac4b7b21bf8a3dc40d26c1e17a06b52e8b76f Id24e47656ae9e1290b22c278e2ab9daaefbfc5e7 I066892b90ae9a3c145eaee84385f7d7b1166d3de Ie63278caae3e30d6a7e7983bb8ede23985e394de I3b47531fc6736dd80aae386b1dbd5bae1667f743 I8bebbdaf44f1a4ffda44b9c1b139d690ccdccf03 I59e872dc6d0d860f8139cd640a8ff0bd2875f1e3 I6f2266eef275d75f033659ffbb2aaf56996fe109 I8c2c43addbf4754cd4fc3692a99764d6f210284e I05c091fc7ac6786a33f23b01a6e5e3232fb24d6f I820dc8deeebab884a281eb34b139d5da2e0ba19d I5ee2edef73a44dd466f7afaeec1ae5e4a725906c I25926ff4ecb9d1caa511e0b88b80e301b39eeebb I43fac33f9cecff6bf48daa193fc7e26d9baf53d9 I59041e3deb4221c0c79ad00a228bc54b9f47b9a0 I8f5ab7bc4485c6110877e4665dc3af04543628dc I98bcf095eccec97574ee3ed30d636f2e1e28bd83 I9abe41d2cc399427daed1168f25ccfba7944ca2a I0fed5a7ae5c78828465fb03fc25f572c98d83855 I4f34366885634988dbd0f0887500f659175977cb I246afd3e92f4842329f9326ead79fcebce8faa3e I8debb8e28fc287f4ccfa12556af8d0dec6b69702 Ic3c4f366a92e3b741a5790c49262c1a619d9aa94 I711efda1a8778f784112993367836c046708cfa8 I268b90252d7e2cf6687dc5efab8e1b5b6d8297cf I3179e8b60353bb6e6c005f0eda0ede99741630d9 I762b84bd46d8be3b0515b960d7cf14d08123e114 I11f70a3704fc12c014abf52ae0499b45df7779dd I0b3f7c64afe726b9dc9a3e2aa900282e719bda93 I673bcf060012f889b3d5a511b5ed16405e31fec7 I1085d81dbf5a2126c28f160969875746217e3caf Icb156e2dbeb4a0ded3f0b09943ac1c0ca07fa70b I23b9610276faea5a3873a29e6cbe4b21c4555553 Ia8c86184fedd497d79fb0583f0554dc27210dbe1 I0e3372075ff0f765f835bf09452b65b00cc76345 I9dce1d78eaabbf087fac1a1964a5f183bb230242 I74ef0cafb94b3a5a48810827f273e663b4f68bf2 I9e44910af2df28687fcc9b1f4e8b4661d5ad416b If9ec37d0d416d645d875b8d815f63896fbc05312 I5660f78324bd2d6763a02bef283292c1ad1c31b7 I45d0caf54fb0db79949f6628eb4a2ab2af43e6ce I6ef0f8d0686c201e26e9112913b1a74d3b8bd2d5 I7a839defea1db441f36f29e5dcdbd83020aec03a Id144c7e227879d1d4814d8a212f6b790f492c231 Ib8cca85a92bcfde3571479482e0b0634c32b364d I665a3756e3f4dbd4ff602879bfb0e43c89810560 I899ce16253ab06ca74b4c9f2de00421f6d806e14 If873eee6f8aa6d25054a44c445a7d7829d975ef9 I90b96f99e13c808411cac284a381886f74bf799c Ifd1436d1ee2bb3cd948bf1f53256dfd3bef057d1 I19327d379967a3a790be5a9109178663089c0cb4 I2241082ffc4202e436d432de051d40a30478d639 I990917cdb1ef0fffe4a8b54794fe2f21eeeedb8e I1bce7e3a9185c9a7713cb80396154dd820e8d349 I3996a7c21adf2d13b55a986b9e043ac7860d979d I75aa1ea47e5623e2e08a94b185f1407005276b84 I89990204c1d796d85f132229b7ea71c50b24c47b I12244463bfafa6eb00156a21181bd70a0d6fc00f Id3a40cd8d472ff4f0437314f65852d27cfea2fc0 I30b87c8b000a9bbe474bc75f1ed42d38a958aa8b Ia55fbc1a4c49cf6e284b8668582e82613c1f4f89 I2166158b1390320a1d7a41cbb582361acc756d2c Ie4850297db76f4357325988d238d8c8cc1c455a9 I8e501b0c0d6714115dfad49e6dafee556e476e64 I7be547a0f360547c28d4f496ab4ae03b1afd405a Ifa85c47f54ee4c8b86a75f59cbe4ce58b47ef318 Ib364f82b5890ad42c52365a1cc0af155378425bb I4993386b60de9c29fc734497c3df2a9e9c5feecc If1060b2559d213964f8f7ad75596fbc38b25da58 I323997c1ef48a79b3ba97642be333ae9c55b080f I5bad6ba75977d0ae40e58d4c057118ecb6cc4e14 I96b8e9b8aa8e818d27e24d74a0953c2cb8e95158 I0f8f4eff4509ce860432bdf47d506ed3d633285d Id5147073f354f096aebe13e46a1e0926dce2d4f9 I8e14aa8b202692153ff980f63a055592255078f5 I201766e20e05787e449fe8c2a44c91e971dbccf5 Icda37244848524301ebafd9d5b666f75d41f5b42 Ia84b999f15a91d6e17025accab3d64f3158b07ec I09c4ac06111ad8f51f537809b397ff990e814dcb)

declare -a COMPONENTS_WITH_CHANGE_ID=()
for change in "${CHANGE_IDs[@]}"; do
    PROJECT=$(ssh -p 29418 $(whoami)@$gerrit gerrit query --patch-sets $change | grep project | awk '{print $2}')
    echo "change" $change ${PROJECT}
   
    if [[ "${COMPONENTS[*]}" =~ "$PROJECT" ]]; then 
        COMPONENTS_WITH_CHANGE_ID+=("$PROJECT")
    fi
done


declare -a COMPONENTS_WITHOUT_CHANGE_ID=()
for component in "${COMPONENTS[@]}"; do
    if [[ ! "${COMPONENTS_WITH_CHANGE_ID[*]}" =~ "$component" ]]; then 
           COMPONENTS_WITHOUT_CHANGE_ID+=("$component")
    fi
done


echo ${COMPONENTS_WITH_CHANGE_ID[@]} 
echo ${COMPONENTS_WITH_CHANGE_ID[@]}  | tr " " "\n" | wc -l

echo ${COMPONENTS_WITHOUT_CHANGE_ID[@]} 
echo ${COMPONENTS_WITHOUT_CHANGE_ID[@]}  | tr " " "\n" | wc -l

echo ${COMPONENTS[@]}  | tr " " "\n" | wc -l

mkdir projects
cd projects

declare -a COMPONENTS_WITH_NEW_CHANGE_ID=()
declare -a COMPONENTS_WITH_NO_BRANCH=()
declare -a COMPONENTS_FAILD_TO_CLONE=()

for component in "${COMPONENTS_WITHOUT_CHANGE_ID[@]}"; do
    random=$( (cat /proc/sys/kernel/random/uuid | sed 's/[-]//g' | head -c 40) | git hash-object --stdin)
    COMMIT_HASH="I"$random
    COMMIT_MSG="DNM [CRE] [OSPCRE-62] - Downstream component jobs

This change is going to be abandined after the zuul job verificarion.

Depends-On: https://$gerrit/gerrit/c/openstack/osp-internal-jobs/+/303197

Change-Id: "$COMMIT_HASH

    rm -rf $component
    if git clone https://$(whoami)@$gerrit/gerrit/$component.git; then
        cd $component
        if git checkout $branch; then
            date > foo
            git add foo

            git commit -a -m "$COMMIT_MSG"
            git review

            echo submitted change for $component with change-ID $COMMIT_HASH
            COMPONENTS_WITH_NEW_CHANGE_ID+=("$COMMIT_HASH")
        else
            echo failed to checkout $branch for $component
            COMPONENTS_WITH_NO_BRANCH+=("$component")
        fi
        cd ..
    else
       echo failed to clone $component
       COMPONENTS_FAILD_TO_CLONE+=("$component")
    fi
done

echo componnets with new change
echo ${COMPONENTS_WITH_NEW_CHANGE_ID[@]} 

echo components failed to clone
echo ${COMPONENTS_FAILD_TO_CLONE[@]}

echo components failed to checkout $branch
echo ${COMPONENTS_WITH_NO_BRANCH[@]}

