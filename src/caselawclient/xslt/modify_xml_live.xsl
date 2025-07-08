<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
    xmlns='http://docs.oasis-open.org/legaldocml/ns/akn/3.0'
    xmlns:akn='http://docs.oasis-open.org/legaldocml/ns/akn/3.0'
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:uk='https://caselaw.nationalarchives.gov.uk/akn'>
    <xsl:param name="work_uri" />
    <xsl:param name="expression_uri" />
    <xsl:param name="manifestation_uri" />
    <xsl:output method="xml" indent="yes" />

    <!-- Identify transformation -->
    <xsl:template match="@* | node()">
        <xsl:copy>
            <xsl:apply-templates select="@* | node()" />
        </xsl:copy>
    </xsl:template>

    <!-- <xsl:template match="akn:identification/FRBRWork/FRBRthistext/text()"><xsl:copy-of select="$cat" /></xsl:template> -->

    <xsl:template match="akn:identification/akn:FRBRWork/akn:FRBRthis">
        <FRBRthis>
            <xsl:attribute name="value">
                <xsl:value-of select="$work_uri" />
            </xsl:attribute>
        </FRBRthis>
    </xsl:template>

    <xsl:template match="akn:identification/akn:FRBRWork/akn:FRBRuri">
        <FRBRuri>
            <xsl:attribute name="value">
                <xsl:value-of select="$work_uri" />
            </xsl:attribute>
        </FRBRuri>
    </xsl:template>

    <xsl:template match="akn:identification/akn:FRBRExpression/akn:FRBRthis">
        <FRBRthis>
            <xsl:attribute name="value">
                <xsl:value-of select="$expression_uri" />
            </xsl:attribute>
        </FRBRthis>
    </xsl:template>

    <xsl:template match="akn:identification/akn:FRBRExpression/akn:FRBRuri">
        <FRBRuri>
            <xsl:attribute name="value">
                <xsl:value-of select="$expression_uri" />
            </xsl:attribute>
        </FRBRuri>
    </xsl:template>

    <xsl:template match="akn:identification/akn:FRBRManifestation/akn:FRBRthis">
        <FRBRthis>
            <xsl:attribute name="value">
                <xsl:value-of select="$manifestation_uri" />
            </xsl:attribute>
        </FRBRthis>
    </xsl:template>

    <xsl:template match="akn:identification/akn:FRBRManifestation/akn:FRBRuri">
        <FRBRuri>
            <xsl:attribute name="value">
                <xsl:value-of select="$manifestation_uri" />
            </xsl:attribute>
        </FRBRuri>
    </xsl:template>


</xsl:stylesheet>
