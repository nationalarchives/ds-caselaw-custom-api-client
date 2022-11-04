from xml.etree import ElementTree

import environ

env = environ.Env()

print(env("MARKLOGIC_HOST"))
from src.caselawclient.Client import api_client

judgment = """
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:html="http://www.w3.org/1999/xhtml" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
  <judgment name="judgment">
    <meta>
      <identification source="#tna">
        <FRBRWork>
          <FRBRthis value="https://caselaw.nationalarchives.gov.uk/id/ewca/crim/2022/1263"/>
          <FRBRuri value="https://caselaw.nationalarchives.gov.uk/id/ewca/crim/2022/1263"/>
          <FRBRdate date="2022-09-16" name="judgment"/>
          <FRBRauthor href="#ewca-criminal"/>
          <FRBRcountry value="GB-UKM"/>
          <FRBRnumber value="1263"/>
          <FRBRname value="R v Andrew William John Vowles"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="https://caselaw.nationalarchives.gov.uk/ewca/crim/2022/1263"/>
          <FRBRuri value="https://caselaw.nationalarchives.gov.uk/ewca/crim/2022/1263"/>
          <FRBRdate date="2022-09-16" name="judgment"/>
          <FRBRauthor href="#ewca-criminal"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="https://caselaw.nationalarchives.gov.uk/ewca/crim/2022/1263/data.xml"/>
          <FRBRuri value="https://caselaw.nationalarchives.gov.uk/ewca/crim/2022/1263/data.xml"/>
          <FRBRdate date="2022-10-28T11:53:19" name="transform"/>
          <FRBRauthor href="#tna"/>
          <FRBRformat value="application/xml"/>
        </FRBRManifestation>
      </identification>
      <lifecycle source="#">
        <eventRef date="2022-09-16" refersTo="#judgment" source="#"/>
      </lifecycle>
      <references source="#tna">
        <TLCOrganization eId="ewca-criminal" href="https://www.gov.uk/courts-tribunals/court-of-appeal-criminal-division" showAs="The Court of Appeal of England and Wales (Criminal Division)" shortForm="Court of Appeal Criminal Division"/>
        <TLCOrganization eId="tna" href="https://www.nationalarchives.gov.uk/" showAs="The National Archives"/>
        <TLCEvent eId="judgment" href="#" showAs="judgment"/>
        <TLCPerson eId="rex" href="" showAs="REX"/>
        <TLCPerson eId="andrew-william-john-vowles" href="" showAs="ANDREW WILLIAM JOHN VOWLES"/>
        <TLCRole eId="before-the-v" href="" showAs="Before The V"/>
        <TLCRole eId="after-the-v" href="" showAs="After The V"/>
        <TLCPerson eId="judge-lord-justice-singh" href="/judge-lord-justice-singh" showAs="LORD JUSTICE SINGH"/>
        <TLCPerson eId="judge-mr-justice-fraser" href="/judge-mr-justice-fraser" showAs="MR JUSTICE FRASER"/>
        <TLCPerson eId="judge-mr-justice-henshaw" href="/judge-mr-justice-henshaw" showAs="MR JUSTICE HENSHAW"/>
      </references>
      <proprietary source="#">
        <uk:court>EWCA-Criminal</uk:court>
        <uk:year>2022</uk:year>
        <uk:number>1263</uk:number>
        <uk:cite>[2022] EWCA Crim 1263</uk:cite>
        <uk:parser>0.10.11</uk:parser>
        <uk:hash>c25db44b94baf69e5f6053dca6e492d7f6abd1fd37ddb0b38d25ecb562334571</uk:hash>
      </proprietary>
      <presentation source="#">
        <html:style>
#judgment { font-family: 'Times New Roman'; font-size: 12pt; }
#judgment .Normal { font-size: 12pt; }
#judgment .Header { font-size: 12pt; }
#judgment .Footer { font-size: 12pt; }
#judgment .CoverText { text-align: right; text-decoration-line: underline; text-decoration-style: solid; font-size: 12pt; }
#judgment .ListParagraph { margin-left: 0.5in; font-size: 12pt; }
#judgment .BalloonText { font-family: Tahoma; font-size: 8pt; }
#judgment .FootnoteText { font-size: 10pt; }
#judgment .Colloquy { margin-left: 0.4in; margin-right: 0.01in; font-family: 'Courier New'; font-size: 12pt; }
#judgment .ContinCol { margin-left: 0.4in; margin-right: 0.01in; font-family: 'Courier New'; font-size: 12pt; }
#judgment .HeaderChar { font-size: 12pt; }
#judgment .FooterChar { font-size: 12pt; }
#judgment .LineNumber { }
#judgment .Hyperlink { text-decoration-line: underline; text-decoration-style: solid; color: #0000FF; }
#judgment .FollowedHyperlink { text-decoration-line: underline; text-decoration-style: solid; color: #800080; }
#judgment .Mention1 { color: #2B579A; background-color: initial; }
#judgment .PageNumber { }
#judgment .BalloonTextChar { font-size: 1pt; }
#judgment .FootnoteTextChar { font-size: 10pt; }
#judgment .FootnoteReference { vertical-align: super; }
#judgment .UnresolvedMention1 { color: #605E5C; background-color: initial; }
#judgment .TableGrid { }
#judgment .TableGrid td { border: 0.5pt solid; }
</html:style>
      </presentation>
    </meta>
    <coverPage>
      <p class="Header" style="text-align:right"/>
    </coverPage>
    <header>
      <table uk:widths="6.68in">
        <tr>
          <td style="border:0.5pt solid">
            <block name="restriction"><span style="font-weight:bold;font-size:10pt">WARNING: reporting restrictions may apply to the contents transcribed in this document, particularly if the case concerned a sexual offence or involved a child. Reporting restrictions prohibit the publication of the applicable information to the public or any section of the public, in writing, in a broadcast or by means of the internet, including social media. Anyone who receives a copy of this transcript is responsible in law for making sure that applicable restrictions are not breached. A person who breaches a reporting restriction is liable to a fine and/or imprisonment. For guidance on whether reporting restrictions apply, and to what information, ask at the court office or take legal advice.</span></block>
          </td>
        </tr>
        <tr>
          <td style="border:0.5pt solid">
            <p style="text-align:justify"><span style="font-weight:bold;font-size:10pt">This Transcript is Crown Copyright.  It may not be reproduced in whole or in part other than in accordance with relevant licence or with the express consent of the Authority.  All rights are reserved.</span></p>
          </td>
        </tr>
      </table>
      <table uk:widths="4.81in 1.88in">
        <tr>
          <td>
            <p style="margin-left:-0.07in"><img src="image1.png" style="width:76.5pt;height:75.75pt"/><courtType refersTo="#ewca-criminal"><span style="text-decoration-line:underline;text-decoration-style:solid">IN THE COURT OF APPEAL</span></courtType></p>
            <p style="margin-left:-0.07in"><courtType refersTo="#ewca-criminal" style="text-decoration-line:underline;text-decoration-style:solid">CRIMINAL DIVISION</courtType></p>
            <p style="margin-left:-0.07in"><neutralCitation style="text-decoration-line:underline;text-decoration-style:solid">[2022] EWCA Crim 1263</neutralCitation></p>
            <p style="text-align:right"/>
            <p style="margin-left:-0.07in"/>
          </td>
          <td>
            <p style="text-align:right"/>
            <p style="text-align:right"><span style="text-decoration-line:underline;text-decoration-style:solid">No. 202200551 A1</span></p>
            <p style="text-align:right"/>
            <p style="text-align:right"/>
          </td>
        </tr>
      </table>
      <p style="text-align:right"><span style="text-decoration-line:underline;text-decoration-style:solid">Royal Courts of Justice</span></p>
      <p style="text-align:right;margin-left:0.4in;text-indent:-0.4in"><docDate date="2022-09-16" refersTo="#judgment" style="text-decoration-line:underline;text-decoration-style:solid">Friday, 16 September 2022</docDate></p>
      <p style="text-align:center">Before:</p>
      <p style="text-align:center"><judge refersTo="#judge-lord-justice-singh" style="text-decoration-line:underline;text-decoration-style:solid">LORD JUSTICE SINGH</judge></p>
      <p style="text-align:center"><judge refersTo="#judge-mr-justice-fraser" style="text-decoration-line:underline;text-decoration-style:solid">MR JUSTICE FRASER</judge></p>
      <p style="text-align:center"><judge refersTo="#judge-mr-justice-henshaw" style="text-decoration-line:underline;text-decoration-style:solid">MR JUSTICE HENSHAW</judge></p>
      <p style="text-align:center"><party refersTo="#rex" as="#before-the-v">REX</party></p>
      <p style="text-align:center">V </p>
      <p style="text-align:center"><party refersTo="#andrew-william-john-vowles" as="#after-the-v">ANDREW WILLIAM JOHN VOWLES</party></p>
      <p style="text-align:center">__________</p>
      <p style="text-align:center;margin-left:0.4in;text-indent:-0.4in">Computer-aided Transcript prepared from the Stenographic Notes of</p>
      <p style="text-align:center;margin-left:0.4in;text-indent:-0.4in">Opus 2 International Ltd.</p>
      <p style="text-align:center">Official Court Reporters and Audio Transcribers</p>
      <p style="text-align:center">5 New Street Square, London, EC4A 3BF<br/>Tel:  020 7831 5627     Fax:  020 7831 7737</p>
      <p style="text-align:center"><span class="Hyperlink" style="color:#000000">CACD.ACO@opus2.digital</span></p>
      <p style="text-align:center">_________</p>
      <p style="text-align:center;margin-left:0.4in;text-indent:-0.4in"><span style="text-decoration-line:underline;text-decoration-style:solid">MR O D P WILLIAMS</span> appeared on behalf of the Appellant.</p>
      <p style="text-align:center"><span style="text-decoration-line:underline;text-decoration-style:solid">MS R KNIGHT</span> appeared on behalf of the Crown.</p>
      <p style="text-align:center">_________</p>
      <p style="text-align:center"><span style="font-weight:bold;text-decoration-line:underline;text-decoration-style:solid">JUDGMENT</span></p>
    </header>
    <judgmentBody>
      <decision>
        <level>
          <content>
            <p>MR JUSTICE FRASER:</p>
          </content>
        </level>
        <paragraph eId="para_1">
          <num style="font-family:'Times New Roman';font-size:12pt;margin-left:0.5in;text-indent:-0.5in">1</num>
          <content>
            <p class="Colloquy" style="margin-left:0.5in;margin-right:0.01in"><span style="font-family:'Times New Roman'">This is an appeal against sentence following the grant of permission by the single Judge.  The appeal has been argued before us this morning on the appellant’s behalf by Mr Williams, who was also counsel for him at the sentencing hearing below.  We are grateful to him for his succinct and realistic submissions.  We have also had the benefit of the attendance on behalf of the Crown from Miss Knight, although we did not find it necessary to call upon her for oral submissions.</span></p>
          </content>
        </paragraph>
        <paragraph eId="para_2">
          <num style="font-family:'Times New Roman';font-size:12pt;margin-left:0.5in;text-indent:-0.5in">2</num>
          <content>
            <p class="ContinCol" style="margin-left:0.5in;margin-right:0.01in"><span style="font-family:'Times New Roman'">On 16 February 2022 in the Crown Court at Cardiff, following an earlier guilty plea by the appellant, HHJ Richard Williams sentenced the appellant to a term of imprisonment of 7 years and 6 months for the offence of causing death by dangerous driving, contrary to section 1 of the Road Traffic Act 1988.  The appellant was also disqualified from driving for a total period of 8 years and 9 months, comprising an extension period to reflect the time that he would spend in custody of 45 months, and an operative disqualification period of 5 years, following his release.  An order for an extended retest was also made.  The appellant was also in breach of a suspended sentence order that had been imposed upon him only one month before this offence, and therefore he was re-sentenced, along with that index offence, on 16 February 2022.  However, that particular sentence, which was activated, was made to run concurrently to the term of imprisonment on the more serious charge. Therefore, it had no effect upon the overall term of imprisonment which he was ordered to serve.  </span></p>
          </content>
        </paragraph>
        <paragraph eId="para_3">
          <num style="font-family:'Times New Roman';font-size:12pt;margin-left:0.5in;text-indent:-0.5in">3</num>
          <content>
            <p class="ContinCol" style="margin-left:0.5in;margin-right:0.01in"><span style="font-family:'Times New Roman'">The person who died as a result of the appellant's dangerous driving was Danielle Andrews.  She was at the time of the offence, which took place on 27 November 2020, 28 years old and she had four small children.  We appreciate that in hearing an appeal of this nature, the victim's family and friends, and members of the public, may feel that a cold and dispassionate discussion has taken place in court that pays limited attention to the central fact that a person, loved by many and sorely missed, has died as a direct result of a criminal offence.  We are anxious to dispel any such impression and wish to make it clear that the court is very much aware that offences such as these, directly involve the death of a real person much loved by family and friends. Nothing that the court can do will either bring her back, or reduce the distress which her family and friends have and will continue to suffer.  </span></p>
          </content>
        </paragraph>
        <paragraph eId="para_4">
          <num style="font-family:'Times New Roman';font-size:12pt;margin-left:0.5in;text-indent:-0.5in">4</num>
          <content>
            <p class="ContinCol" style="margin-left:0.5in;margin-right:0.01in"><span style="font-family:'Times New Roman'">The facts of the appellant's offending are as follows.  On the evening of 27 November </span><br/><span style="font-family:'Times New Roman'">2020 Miss Andrews and the appellant, who were in a relationship together, checked into a hotel for the weekend in Cardiff city centre.  The appellant had collected her in his Volkswagen Golf motor car and there is CCTV footage which shows them arriving and parking at the hotel.  During the course of the night there was some sort of disturbance within their hotel room and complaints were made about the noise by other customers of the hotel.  A fire alarm was activated within their room.  Following a discussion with the hotel staff, the two of them decided to leave and at about 3.45 a.m. in the early morning of the next day they left together in the appellant's car.  They drove together through the deserted city centre of Cardiff.  Text messages on one of the appellant's phones showed that he had arranged to buy some more cocaine, cocaine having been consumed by them earlier in the evening.  It was raining very heavily. Nobody knows exactly what took place in the hotel room between them, or the nature of relations between them when they left. The next morning the hotel staff found both a broken mirror, and blood, in the hotel room, but by then Miss Andrews was dead.</span></p>
          </content>
        </paragraph>
        <paragraph eId="para_5">
          <num style="font-family:'Times New Roman';font-size:12pt;margin-left:0.5in;text-indent:-0.5in">5</num>
          <content>
            <p class="ContinCol" style="margin-left:0.5in;margin-right:0.01in"><span style="font-family:'Times New Roman'">There is CCTV footage of their journey through the city centre and it is obvious to the court from viewing that footage that the appellant, who was driving the car, was doing so at some increasing speed, if not somewhat erratically.  The roads were deserted, but the car can be seen driving in the middle of the road, partly on the opposite carriageway, and at what appears to be in excess of the speed limit. Regardless of the driving in the city centre itself, there can be no doubt about what then occurred. At around 4.06 a.m. the appellant was driving the car along a slip road which takes one off the A470. The slip road itself has a speed limit of 40 miles per hour or mph.  The slip road is 250 metres long and rises upwards, where it then turns to the left at the end of the slip road. Here, there are traffic lights where the slip road meets the main gyratory or roundabout system. Those traffic lights had been showing a red signal for 14 seconds, and the appellant drove towards them, up the slip road at speeds of between 62 and 64 mph. This is, self-evidently, very much in excess of the 40 mph speed limit, and paying no attention to the red light.  Rather than negotiate the bend, and come to a stop at the red light, the appellant continued to drive in a straight line making no attempt to navigate around the left hand bend. He made no attempt to brake either, and continued onwards in a straight direction, hitting the kerb where the road bends to the left.  This caused the appellant's vehicle to cross a stretch of grass, before becoming airborne, narrowly missing an upright post.  The car was, quite literally, launched into the air.  The vehicle continued at speed, through the air, across two lanes perpendicular to its direction of travel, any traffic on those lanes having the benefit of a green traffic signal.  Luckily, there were no cars on those two lanes of traffic.  </span></p>
          </content>
        </paragraph>
        <paragraph eId="para_6">
          <num style="font-family:'Times New Roman';font-size:12pt;margin-left:0.5in;text-indent:-0.5in">6</num>
          <content>
            <p class="ContinCol" style="margin-left:0.5in;margin-right:0.01in"><span style="font-family:'Times New Roman'">The Volkswagen Golf continued through the air, and subsequently collided with the grass verge and heavy metal railings or crash barrier on the other side of the two lanes, this crash barrier being demolished in the process.  The main impact to the car was on the front passenger side of the vehicle.  The car then continued at around 43 miles an hour through the crash barrier and was now launched from the top of what is a very steep bank, of about seven metres in depth, into dense woodland on the other side of the road.  It rotated forward clockwise, and collided with large trees until it came to rest on its roof upside down.  Once again, the heaviest impact had been on the front passenger side of the vehicle.  All of this is captured on CCTV, which the court has viewed.  It is very shocking to watch – the car appears at speed, launches into the air, crosses the two lanes whilst airborne and crashes down the bank and into the trees. The photographs of the damaged vehicle show the effects of the very considerable impact and the extensive damage that was caused to the car. The total distance travelled by the car after it first hit the kerb, until it came to rest, was 65 metres.  That distance clearly demonstrates the high speed with which the Golf drove along the slip road and drove straight on, which is what launched it into the air. The wheels were not in contact with the road after that, and so its subsequent course of crossing the other two lanes of traffic, going through the crash barrier and crashing down into the trees was all the effect of the momentum that the car had at the time it hit the kerb.</span></p>
          </content>
        </paragraph>
        <paragraph eId="para_7">
          <num style="font-family:'Times New Roman';font-size:12pt;margin-left:0.5in;text-indent:-0.5in">7</num>
          <content>
            <p class="ContinCol" style="margin-left:0.5in;margin-right:0.01in"><span style="font-family:'Times New Roman'">The appellant, who freed himself from the vehicle despite some injuries, managed to flag down a passing HGV driver about 20 minutes after the car landed.  Miss Andrews was killed in the impact.  Within a few minutes of the HGV being stopped, an off-duty local traffic police officer also passed the scene, stopped and called for assistance and shortly afterwards other police colleagues arrived and the vehicle was located.  The vehicle was so badly crushed that it was difficult to remove Miss Andrews at the time even when her seatbelt was cut. She was pronounced deceased at the scene at around 5.10 a.m.  </span></p>
          </content>
        </paragraph>
        <paragraph eId="para_8">
          <num style="font-family:'Times New Roman';font-size:12pt;margin-left:0.5in;text-indent:-0.5in">8</num>
          <content>
            <p class="ContinCol" style="margin-left:0.5in;margin-right:0.01in"><span style="font-family:'Times New Roman'">The appellant was subsequently conveyed to hospital to treat his injuries and blood samples were taken.  Toxicology evidence showed that the appellant had recently taken cocaine and there was a reading of 254 micrograms of cocaine per litre of blood, 50 micrograms per litre being the legal limit.  Although there was alcohol in his blood, he was within the legal limit for alcohol when driving.  The car was examined and there was no evidence that there was any mechanical defect which could have been a contributory factor to the collision.  </span></p>
          </content>
        </paragraph>
        <paragraph eId="para_9">
          <num style="font-family:'Times New Roman';font-size:12pt;margin-left:0.5in;text-indent:-0.5in">9</num>
          <content>
            <p class="ContinCol" style="margin-left:0.5in;margin-right:0.01in"><span style="font-family:'Times New Roman'">On 4 December 2020 he was released from hospital and was arrested by the police.  In interview the appellant gave no explanation for the fatal collision and subsequently answered "no comment" to questions asked by the police.  At a second interview the appellant also answered "no comment".  The circumstances in which the appellant came to drive straight on, at a speed of over 60 mph on the slip road, ignoring both the speed limit of 40 mph, the red light </span><span style="font-style:italic;font-family:'Times New Roman'">and</span><span style="font-family:'Times New Roman'"> the approaching left-hand bend are entirely unclear both then and indeed now.  There has been no explanation for this driving provided by the appellant and he has made no attempt to assist the crash investigation by answering the questions that were put to him by the police. </span></p>
          </content>
        </paragraph>
        <paragraph eId="para_10">
          <num style="font-family:'Times New Roman';font-size:12pt;margin-left:0.5in;text-indent:-0.5in">10</num>
          <content>
            <p class="ContinCol" style="margin-left:0.5in;margin-right:0.01in"><span style="font-family:'Times New Roman'">Turning to his previous convictions, he had three convictions for six unrelated offences, spanning from 20 May 2020 to 28 October 2020. His previous convictions included the offences for which he was in breach of a suspended sentence order, and he was re-sentenced for that along with the index offence on 16 February 2022.  The suspended sentence order had been imposed upon him for harassment and breach of a restraining order in respect of his former partner, and for destroying and damaging her property.  It was imposed by Gwent Magistrates, and in fact, during 2020, as we have observed, he had been before the courts on a number of occasions in May and August and also in October 2020.  He also had nine penalty points on his licence, three of which were for speeding and six of which were for driving whilst uninsured.</span></p>
          </content>
        </paragraph>
        <paragraph eId="para_11">
          <num style="font-family:'Times New Roman';font-size:12pt;margin-left:0.5in;text-indent:-0.5in">11</num>
          <content>
            <p class="ContinCol" style="margin-left:0.5in;margin-right:0.01in"><span style="font-family:'Times New Roman'">The Pre-sentence Report noted that the appellant claimed not to be able to remember the incident and that he was working in the London area during the week as a water engineer, and he had a good work record prior to the events.  His injuries from the accident had led to his work situation changing, and as a result, he was at that point in receipt of benefits.  He admitted to substance abuse over a number of years but did not accept that his cocaine use that night would have affected his driving.  </span></p>
          </content>
        </paragraph>
        <paragraph eId="para_12">
          <num style="font-family:'Times New Roman';font-size:12pt;margin-left:0.5in;text-indent:-0.5in">12</num>
          <content>
            <p class="ContinCol" style="margin-left:0.5in;margin-right:0.01in"><span style="font-family:'Times New Roman'">The sentencing judge also had the victim personal statement from Angela Morgan before him, which he considered.  The sentencing judge explained that in his judgment this was an offence of level 1 culpability and that the manner in which the vehicle was driven in the place that it was driven, and in those circumstances, justified the finding that this was driving in flagrant disregard for the rules of the road.  It was, in any event, agreed between the parties that this was driving within Category 1 of the definitive guideline.  Before considering any additional aggravating or mitigating factors or credit for plea, the sentencing judge took the start point provided by the guideline of eight years' imprisonment and then included as aggravating factors that the appellant was subject to a recently imposed suspended sentence and that he had significant levels of cocaine breakdown products in his blood. The judge considered that these features required an increase in sentence to ten years.  He then applied the discount for the plea of guilty which had not been tendered at the earliest opportunity but still justified a reduction of 25 per cent.</span></p>
          </content>
        </paragraph>
        <paragraph eId="para_13">
          <num style="font-family:'Times New Roman';font-size:12pt;margin-left:0.5in;text-indent:-0.5in">13</num>
          <content>
            <p class="ContinCol" style="margin-left:0.5in;margin-right:0.01in"><span style="font-family:'Times New Roman'">The grounds of appeal are twofold.  Firstly, it is said by Mr Williams that the starting point taken by the judge, by which he means the ten years prior to discount for plea, was well in excess of the starting point for the level 1 offence of eight years.  Secondly, it is said that the resulting seven years, six months' prison sentence is manifestly excessive.  </span></p>
          </content>
        </paragraph>
        <paragraph eId="para_14">
          <num style="font-family:'Times New Roman';font-size:12pt;margin-left:0.5in;text-indent:-0.5in">14</num>
          <content>
            <p class="ContinCol" style="margin-left:0.5in;margin-right:0.01in"><span style="font-family:'Times New Roman'">The second ground is the test that will be applied by this court on an appeal against sentence.  Essentially, what is said is that the sentencing judge double counted by reaching 10 years on the basis that the cocaine use was one of those features which categorised this offence as falling within level 1.  It is sensibly accepted by Mr Williams that the figure for discount of 25 per cent cannot be challenged. </span></p>
          </content>
        </paragraph>
        <paragraph eId="para_15">
          <num style="font-family:'Times New Roman';font-size:12pt;margin-left:0.5in;text-indent:-0.5in">15</num>
          <content>
            <p class="ContinCol" style="margin-left:0.5in;margin-right:0.01in"><span style="font-family:'Times New Roman'">We are grateful to Mr Williams for his submissions, who sought to persuade us that the resulting sentence of seven years, six months is manifestly excessive and that the judge moved too high within the range for this category of offence.</span></p>
          </content>
        </paragraph>
        <paragraph eId="para_16">
          <num style="font-family:'Times New Roman';font-size:12pt;margin-left:0.5in;text-indent:-0.5in">16</num>
          <content>
            <p class="ContinCol" style="margin-left:0.5in;margin-right:0.01in"><span style="font-family:'Times New Roman'">We are, however, entirely unpersuaded by those submissions.  This was, in our judgment, a dreadful piece of highly dangerous driving that was entirely correctly described by the judge as showing a flagrant disregard for the rules of the road, involving as it is did excessive speed and at night in very heavy rain.  The failure even to attempt to turn to the left as the slip road moved round to the left to the red traffic light, and also ignoring the red traffic light completely, would of themselves as features of driving lead to that conclusion, a point which Mr Williams sensibly accepted.  </span></p>
          </content>
        </paragraph>
        <paragraph eId="para_17">
          <num style="font-family:'Times New Roman';font-size:12pt;margin-left:0.5in;text-indent:-0.5in">17</num>
          <intro>
            <p class="ContinCol" style="margin-left:0.5in;margin-right:0.01in"><span style="font-family:'Times New Roman'">Indeed, the guidelines themselves, when explaining the determinants of seriousness, state: </span></p>
          </intro>
          <subparagraph>
            <content>
              <p class="ContinCol" style="margin-left:1in;margin-right:0.78in;text-indent:0in"><span style="font-family:'Times New Roman'">"[...] a prolonged, persistent and deliberate course of very bad driving AND/OR consumption of substantial amounts of alcohol or drugs</span><span style="font-weight:bold;font-family:'Times New Roman'"> </span><span style="font-family:'Times New Roman'">leading to gross impairment [...]" will be determinants that place the case in level 1.  </span></p>
            </content>
          </subparagraph>
          <subparagraph>
            <content>
              <p class="ContinCol" style="margin-left:0.5in;margin-right:0.01in;text-indent:0in"><span style="font-family:'Times New Roman'">Here, in our judgment, the deliberate course of very bad driving puts this as a level 1 offence absent the drug use.  </span></p>
            </content>
          </subparagraph>
        </paragraph>
        <paragraph eId="para_18">
          <num style="font-family:'Times New Roman';font-size:12pt;margin-left:0.5in;text-indent:-0.5in">18</num>
          <content>
            <p class="ContinCol" style="margin-left:0.5in;margin-right:0.01in"><span style="font-family:'Times New Roman'">As correctly noted by the judge, there are two significant additional aggravating factors.  Firstly, the appellant was in breach of the suspended sentence order that had been imposed upon him only one month before.  Correctly, in terms of the consideration of totality, having ordered that to be served concurrently, the only way that aggravating factor could be reflected was by increasing the sentence on the count of causing death by dangerous driving.  Secondly, not only had the appellant been using cocaine that evening, but when his blood was analysed at the hospital, the toxicology evidence showed that the amount of cocaine in his bloodstream was over five times higher than the legal limit.  That is a separate significant aggravating factor, and in our judgment, was properly reflected with a further increase above the level 1 starting point.  Both of these significant factors had to be taken into account by increasing the sentence. They could not sensibly, and should not have been, ignored. The sentencing judge needed to take them into account, and properly did so, explaining his reasoning, and applying the increase to the sentence that he considered they merited.</span></p>
          </content>
        </paragraph>
        <paragraph eId="para_19">
          <num style="font-family:'Times New Roman';font-size:12pt;margin-left:0.5in;text-indent:-0.5in">19</num>
          <content>
            <p class="ContinCol" style="margin-left:0.5in;margin-right:0.01in"><span style="font-family:'Times New Roman'">In our judgment, the sentencing judge carefully considered all the relevant circumstances of this tragic case and conducted a careful sentencing exercise that correctly reflected the aggravating factors. This resulted in a sentence which, in our judgment, cannot be faulted.  It is not a sentence that we consider can be described as manifestly excessive and there is no basis for it to be disturbed by this appellate court.  </span></p>
          </content>
        </paragraph>
        <paragraph eId="para_20">
          <num style="font-family:'Times New Roman';font-size:12pt;margin-left:0.5in;text-indent:-0.5in">20</num>
          <content>
            <p class="ContinCol" style="margin-left:0.5in;margin-right:0.01in"><span style="font-family:'Times New Roman'">It follows, therefore, that in those circumstances the appeal is dismissed. </span></p>
          </content>
        </paragraph>
        <level>
          <content>
            <p class="ListParagraph" style="text-align:center;margin-left:0in">__________</p>
          </content>
        </level>
        <level>
          <content>
            <p/>
          </content>
        </level>
      </decision>
    </judgmentBody>
  </judgment>
</akomaNtoso>
"""

judgment_xml = ElementTree.fromstring(judgment)

response = api_client.insert_judgment_xml("ewca/crim/2022/1263", judgment_xml)
print(response)
