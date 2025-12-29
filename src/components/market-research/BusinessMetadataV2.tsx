import React from 'react';
import { Mail, Phone, MapPin, Facebook, Twitter, Linkedin, Instagram } from 'lucide-react';

interface BusinessMetadataV2Props {
    businessDetails?: {
        contact_info?: {
            email?: string;
            phone?: string;
            address?: string;
        };
        social_links?: {
            facebook?: string;
            twitter?: string;
            linkedin?: string;
            instagram?: string;
        };
    };
}

const BusinessMetadataV2: React.FC<BusinessMetadataV2Props> = ({ businessDetails }) => {
    // Hide if no enhanced business details
    if (!businessDetails?.contact_info && !businessDetails?.social_links) {
        return null;
    }

    const { contact_info, social_links } = businessDetails;

    const contactItems = [
        {
            icon: Mail,
            label: 'Email',
            value: contact_info?.email,
            href: contact_info?.email ? `mailto:${contact_info.email}` : null,
        },
        {
            icon: Phone,
            label: 'Phone',
            value: contact_info?.phone,
            href: contact_info?.phone ? `tel:${contact_info.phone}` : null,
        },
        {
            icon: MapPin,
            label: 'Address',
            value: contact_info?.address,
            href: null,
        },
    ];

    const socialPlatforms = [
        { icon: Facebook, name: 'Facebook', url: social_links?.facebook },
        { icon: Twitter, name: 'Twitter', url: social_links?.twitter },
        { icon: Linkedin, name: 'LinkedIn', url: social_links?.linkedin },
        { icon: Instagram, name: 'Instagram', url: social_links?.instagram },
    ];

    const hasSocialLinks = socialPlatforms.some((p) => p.url);

    return (
        <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">Enhanced Business Metadata</h3>

            {/* Contact Information */}
            {contact_info && (
                <div className="mb-6">
                    <h4 className="text-sm font-semibold text-gray-300 mb-3">Contact Information</h4>
                    <div className="space-y-2">
                        {contactItems.map((item) => {
                            const Icon = item.icon;
                            return (
                                <div key={item.label} className="flex items-center gap-2">
                                    <Icon size={16} className="text-blue-400" />
                                    <span className="text-sm font-medium text-gray-400 min-w-[60px]">
                                        {item.label}:
                                    </span>
                                    {item.value ? (
                                        item.href ? (
                                            <a
                                                href={item.href}
                                                className="text-sm text-blue-400 hover:text-blue-300 hover:underline"
                                                target={item.label === 'Email' || item.label === 'Phone' ? undefined : '_blank'}
                                                rel={item.label === 'Email' || item.label === 'Phone' ? undefined : 'noopener noreferrer'}
                                            >
                                                {item.value}
                                            </a>
                                        ) : (
                                            <span className="text-sm text-white">{item.value}</span>
                                        )
                                    ) : (
                                        <span className="text-sm text-gray-500">—</span>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Social Presence */}
            {hasSocialLinks && (
                <div>
                    <h4 className="text-sm font-semibold text-gray-300 mb-3">Social Presence</h4>
                    <div className="flex items-center gap-3">
                        {socialPlatforms.map(
                            (platform) =>
                                platform.url && (
                                    <a
                                        key={platform.name}
                                        href={platform.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-blue-400 hover:text-blue-300 transition-colors"
                                        title={platform.name}
                                    >
                                        <platform.icon size={20} />
                                    </a>
                                )
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default BusinessMetadataV2;
