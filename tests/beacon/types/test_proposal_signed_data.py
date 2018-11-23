from eth.beacon.types.proposal_signed_data import (
    ProposalSignedData,
)


def test_defaults(sample_proposal_signed_data_params):
    proposal_signed_data = ProposalSignedData(**sample_proposal_signed_data_params)
    assert proposal_signed_data.fork_version == sample_proposal_signed_data_params['fork_version']
    assert proposal_signed_data.slot == sample_proposal_signed_data_params['slot']
    assert proposal_signed_data.shard == sample_proposal_signed_data_params['shard']
    assert proposal_signed_data.block_hash == sample_proposal_signed_data_params['block_hash']
