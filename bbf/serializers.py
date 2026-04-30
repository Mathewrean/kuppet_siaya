from rest_framework import serializers
from .models import BBFClaim, BBFBeneficiary
from accounts.models import CustomUser


class BBFBeneficiarySerializer(serializers.ModelSerializer):
    required_document_name = serializers.ReadOnlyField()
    
    class Meta:
        model = BBFBeneficiary
        fields = [
            'id', 'beneficiary_type', 'full_name', 'document', 
            'document_status', 'approved_by', 'approved_at', 'required_document_name'
        ]
        read_only_fields = ['id', 'document_status', 'approved_by', 'approved_at']


class BBFClaimSerializer(serializers.ModelSerializer):
    beneficiaries = BBFBeneficiarySerializer(many=True, read_only=True)
    member_name = serializers.SerializerMethodField()
    
    class Meta:
        model = BBFClaim
        fields = [
            'id', 'claim_reference', 'member', 'member_name', 'status',
            'submitted_at', 'updated_at', 'beneficiaries_count', 'beneficiaries',
            'subcounty_confirmed_at', 'county_confirmed_at'
        ]
        read_only_fields = ['id', 'claim_reference', 'status', 'submitted_at', 'updated_at']
    
    def get_member_name(self, obj):
        return obj.member.get_full_name()


class BBFClaimCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BBFClaim
        fields = []  # No fields needed for creation, member is set from request
    
    def create(self, validated_data):
        validated_data['member'] = self.context['request'].user
        validated_data['status'] = 'pending'
        return super().create(validated_data)


class BBFBeneficiaryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BBFBeneficiary
        fields = ['beneficiary_type', 'full_name', 'document']
    
    def validate(self, data):
        claim = self.context['claim']
        beneficiary_type = data.get('beneficiary_type')
        
        # Business rules for max beneficiaries
        if beneficiary_type == 'child':
            child_count = claim.beneficiaries.filter(beneficiary_type='child').count()
            if child_count >= 5:
                raise serializers.ValidationError({
                    'beneficiary_type': 'Maximum of 5 children allowed'
                })
        elif beneficiary_type == 'spouse':
            if claim.beneficiaries.filter(beneficiary_type='spouse').exists():
                raise serializers.ValidationError({
                    'beneficiary_type': 'Only one spouse allowed per claim'
                })
        elif beneficiary_type == 'parent_mother':
            if claim.beneficiaries.filter(beneficiary_type='parent_mother').exists():
                raise serializers.ValidationError({
                    'beneficiary_type': 'Only one mother allowed per claim'
                })
        elif beneficiary_type == 'parent_father':
            if claim.beneficiaries.filter(beneficiary_type='parent_father').exists():
                raise serializers.ValidationError({
                    'beneficiary_type': 'Only one father allowed per claim'
                })
        
        # Check document is uploaded
        if not data.get('document'):
            raise serializers.ValidationError({
                'document': f'Document required for {dict(BBFBeneficiary.BENEFICIARY_TYPE_CHOICES).get(beneficiary_type, "beneficiary")}'
            })
        
        return data